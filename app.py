from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from processor import process_channel
import os

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client.youtube_data
canais_col = db.canais

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["channel_url"]
        try:
            channel_id = process_channel(url)
            return redirect(url_for("canal", channel_id=channel_id))
        except Exception as e:
            return f"Erro: {e}"
    canais = list(canais_col.find({}, {"title": 1, "channel_id": 1}))
    return render_template("index.html", canais=canais)

@app.route('/canal/<channel_id>')
def canal(channel_id):
    canal = canais_col.find_one({"channel_id": channel_id})
    return render_template("canal.html", canal=canal)

@app.route('/playlist/<channel_id>/<playlist_id>')
def playlist(channel_id, playlist_id):
    canal = canais_col.find_one({"channel_id": channel_id})
    playlist = next((p for p in canal.get("playlists", []) if p["playlist_id"] == playlist_id), None)
    return render_template("playlist.html", playlist=playlist, canal=canal)

if __name__ == '__main__':
    app.run(debug=True)
