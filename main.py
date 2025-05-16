from dotenv import load_dotenv
from youtool import YouTube
import os
from pymongo import MongoClient

load_dotenv()

def main():
    # Configuração do YouTube API
    api_key = os.getenv("YOUTUBE_API_KEY")
    api_keys = [api_key]
    yt = YouTube(api_keys, disable_ipv6=True)

    # Configuração do MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client.youtube_data
    canais_col = db.canais

    try:
        channel_url = "https://youtube.com/c/PythonparaZumbis/"
        channel_id = yt.channel_id_from_url(channel_url)
        print(f"ID do canal: {channel_id}")

        canais_infos = list(yt.channels_infos([channel_id]))
        canal_info = canais_infos[0] if canais_infos else {}

        canal_doc = {
            "channel_id": channel_id,
            "title": canal_info.get("title", ""),
            "description": canal_info.get("description", ""),
            "playlists": []
        }

        playlists = yt.channel_playlists(channel_id)
        for playlist in playlists:
            print(f"Processando playlist: {playlist['title']}")

            videos = list(yt.playlist_videos(playlist["id"]))
            video_ids = [video['id'] for video in videos]
            videos_full = list(yt.videos_infos(video_ids))

            playlist_doc = {
                "playlist_id": playlist["id"],
                "title": playlist["title"],
                "videos": []
            }

            for video in videos_full:
                print(f"  Processando vídeo: {video['title']}")

                video_id = video['id']

                try:
                    comments = list(yt.video_comments(video_id))
                except Exception as e:
                    print(f"    Comentários desativados ou erro para vídeo {video_id}: {e}")
                    comments = []

                video_doc = {
                    "video_id": video_id,
                    "title": video.get("title", ""),
                    "duration": video.get("duration", ""),
                    "description": video.get("description", ""),
                    "comments": []
                }

                for comment in comments[:5]:
                    video_doc["comments"].append({
                        "author": comment.get("author_display_name", "Anônimo"),
                        "text": comment.get("text_display", ""),
                        "like_count": comment.get("like_count", 0),
                        "published_at": comment.get("published_at", "")
                    })

                playlist_doc["videos"].append(video_doc)

            canal_doc["playlists"].append(playlist_doc)

        canais_col.update_one(
            {"channel_id": channel_id},
            {"$set": canal_doc},
            upsert=True
        )

        print("Dados salvos no MongoDB com sucesso!")

    except Exception as e:
        print(f"Erro ao acessar dados do YouTube ou salvar no MongoDB: {e}")

if __name__ == "__main__":
    main()
