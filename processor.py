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

            try:
                comments = list(yt.video_comments(video_id))
                print(f"Comentário de vídeo {video_id}: {len(comments)} encontrados")
                for comment in comments:
                    base_comment = {
                        "author": comment.get("author", "Anônimo"),
                        "text": comment.get("text", "[sem conteúdo]"),
                        "like_count": comment.get("like_count", 0),
                        "published_at": comment.get("published_at", ""),
                        "replies": []
                    }

                    replies = comment.get("replies")
                    if isinstance(replies, list):
                        for reply in replies:
                            base_comment["replies"].append({
                                "author": reply.get("author", "Anônimo"),
                                "text": reply.get("text", "[sem conteúdo]"),
                                "like_count": reply.get("like_count", 0),
                                "published_at": reply.get("published_at", "")
                            })

                    print(base_comment)
                    video_doc["comments"].append(base_comment)

            except Exception as e:
                print(f"Erro ao buscar comentários do vídeo {video_id}: {e}")

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
