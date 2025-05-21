from youtool import YouTube
from pymongo import MongoClient
from webvtt import WebVTT
import tempfile
import os
import re
from difflib import SequenceMatcher
from dotenv import load_dotenv
import nltk
from nltk.tokenize import sent_tokenize

load_dotenv()
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab')


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def clean_redundant_lines_advanced(lines, similarity_threshold=0.85):
    cleaned = []
    last_sentence = ""

    # Junta blocos quebrados e remove repetições internas
    buffer = ""
    for line in lines:
        line = re.sub(r'\s+', ' ', line.strip())

        if not line or len(line) < 5:
            continue

        # Junta em buffer, pois VTT costuma quebrar no meio de frases
        if buffer:
            buffer += " " + line
        else:
            buffer = line

        if re.search(r'[.!?…]$', line):  # Considera fim de frase
            sentences = sent_tokenize(buffer)

            for s in sentences:
                s = s.strip()

                # Remove repetições de palavras consecutivas
                words = s.split()
                dedup = [words[0]] if words else []
                for word in words[1:]:
                    if word != dedup[-1]:
                        dedup.append(word)
                sentence = ' '.join(dedup)

                # Remove frases muito similares à anterior
                if last_sentence and similar(sentence.lower(), last_sentence.lower()) > similarity_threshold:
                    continue

                cleaned.append(sentence)
                last_sentence = sentence

            buffer = ""

    # Trata frase restante no buffer
    if buffer:
        for s in sent_tokenize(buffer):
            s = s.strip()
            if len(s) > 5 and (not last_sentence or similar(s.lower(), last_sentence.lower()) < similarity_threshold):
                cleaned.append(s)

    final_text = ' '.join(cleaned)
    final_text = re.sub(r'\s([?.!"])', r'\1', final_text)

    return final_text.strip()


def download_and_clean_transcription(yt, video_id):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            downloaded = next(yt.download_transcriptions([video_id], language_code="pt", path=tmp_dir))
            if downloaded["status"] == "done":
                vtt_path = downloaded["filename"]
                vtt = WebVTT().read(vtt_path)

                raw_lines = [caption.text.strip() for caption in vtt if caption.text.strip()]
                clean_text = clean_redundant_lines_advanced(raw_lines)
                return clean_text
    except Exception as e:
        print(f"Erro ao processar transcrição de {video_id}: {e}")
        return ""
    return ""


def process_channel(channel_url):
    api_keys = [os.getenv("YOUTUBE_API_KEY")]
    yt = YouTube(api_keys, disable_ipv6=True)

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client.youtube_data
    canais_col = db.canais

    channel_id = yt.channel_id_from_url(channel_url)
    canais_infos = list(yt.channels_infos([channel_id]))
    canal_info = canais_infos[0] if canais_infos else {}

    canal_base = {
        "channel_id": channel_id,
        "title": canal_info.get("title", ""),
        "description": canal_info.get("description", "")
    }

    canais_col.update_one(
        {"channel_id": channel_id},
        {"$set": canal_base, "$setOnInsert": {"playlists": []}},
        upsert=True
    )

    playlists = yt.channel_playlists(channel_id)
    for playlist in playlists:
        videos = list(yt.playlist_videos(playlist["id"]))
        video_ids = [video['id'] for video in videos]
        videos_full = list(yt.videos_infos(video_ids))

        playlist_doc = {
            "playlist_id": playlist["id"],
            "title": playlist["title"],
            "videos": []
        }

        for video in videos_full:
            video_id = video['id']

            video_doc = {
                "video_id": video_id,
                "title": video.get("title", ""),
                "duration": video.get("duration", ""),
                "description": video.get("description", ""),
                "comments": [],
            }

            transcription_text = download_and_clean_transcription(yt, video_id)
            if transcription_text:
                video_doc["transcription"] = transcription_text

            try:
                comments = list(yt.video_comments(video_id))
                for comment in comments[:5]:
                    video_doc["comments"].append({
                        "author": comment.get("author_name", "Anônimo"),
                        "text": comment.get("text", "[sem conteúdo]"),
                        "like_count": comment.get("like_count", 0),
                        "published_at": comment.get("published_at", "")
                    })
            except:
                pass

            playlist_doc["videos"].append(video_doc)

        # Remove qualquer playlist com mesmo ID
        canais_col.update_one(
            {"channel_id": channel_id},
            {"$pull": {"playlists": {"playlist_id": playlist["id"]}}}
        )

        # Insere a versão nova e atualizada da playlist
        canais_col.update_one(
            {"channel_id": channel_id},
            {"$push": {"playlists": playlist_doc}}
        )
    return channel_id
