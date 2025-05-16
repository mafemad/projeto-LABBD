from dotenv import load_dotenv
from youtool import YouTube
import os

load_dotenv()

api_key = os.getenv("YOUTUBE_API_KEY")
api_keys = [api_key]
yt = YouTube(api_keys, disable_ipv6=True)

channel_id = yt.channel_id_from_url("https://youtube.com/c/PythonparaZumbis/")
print(f"ID do canal: {channel_id}")

playlists = yt.channel_playlists(channel_id)
for playlist in playlists:
    print(f"Playlist: {playlist['title']}")
    videos = yt.playlist_videos(playlist["id"])
    for video in videos:
        print(f"  Vídeo: {video['title']}")
