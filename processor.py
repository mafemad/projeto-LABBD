# processor.py
from youtool import YouTube
from pymongo import MongoClient
from webvtt import WebVTT
import tempfile
import os
import re
from dotenv import load_dotenv

load_dotenv()

def clean_redundant_lines(lines):
    cleaned = []
    last_line = ""

    for line in lines:
        line = line.strip()

        if line == last_line:
            continue
        if len(line) < 5:
            continue

        words = line.split()
        dedup = []
        for i, word in enumerate(words):
            if i == 0 or word != words[i - 1]:
                dedup.append(word)
        cleaned_line = ' '.join(dedup)

        # Evita linhas muito semelhantes à anterior
        if cleaned_line.lower() == last_line.lower():
            continue

        cleaned.append(cleaned_line)
        last_line = cleaned_line

    return cleaned

def download_and_clean_transcription(yt, video_id):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            downloaded = next(yt.download_transcriptions([video_id], language_code="pt", path=tmp_dir))
            if downloaded["status"] == "done":
                vtt_path = downloaded["filename"]
                vtt = WebVTT().read(vtt_path)

                # Extrair linhas limpas
                raw_lines = [caption.text.strip() for caption in vtt if caption.text.strip()]
                lines = clean_redundant_lines(raw_lines)

                # Junta com pontuação básica e quebra de linha lógica
                clean_text = '. '.join(lines)
                clean_text = re.sub(r'\s+', ' ', clean_text)  # normaliza espaços
                clean_text = re.sub(r'\.\s*\.', '.', clean_text)  # evita '..'
                return clean_text.strip()
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

        canais_col.update_one(
            {"channel_id": channel_id},
            {"$push": {"playlists": playlist_doc}}
        )

    return channel_id
