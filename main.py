"""
🎵 Aurafy - A Minimalist Spotify Controller
Author: Param Sangani
"""

import os
import requests
from io import BytesIO
from threading import Timer
from dataclasses import dataclass
from PIL import Image, ImageTk
import tkinter as tk
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class SpotifyCredentials:
    client_id: str
    client_secret: str
    redirect_uri: str = "https://example.org"
    scope: str = (
        "user-read-playback-state user-modify-playback-state "
        "playlist-modify-public playlist-modify-private user-top-read"
    )

class SpotifyClient:
    def __init__(self, creds: SpotifyCredentials):
        self.spotify = Spotify(
            auth_manager=SpotifyOAuth(
                client_id=creds.client_id,
                client_secret=creds.client_secret,
                redirect_uri=creds.redirect_uri,
                scope=creds.scope
            )
        )

    def get_current_track(self):
        current = self.spotify.currently_playing()
        if not current or not current.get("item"):
            return None
        return {
            "title": current["item"]["name"],
            "artist": current["item"]["artists"][0]["name"],
            "album_art": current["item"]["album"]["images"][0]["url"]
        }

    def control(self, action: str):
        try:
            actions = {
                "play": self.spotify.start_playback,
                "pause": self.spotify.pause_playback,
                "next": self.spotify.next_track,
                "prev": self.spotify.previous_track,
                "repeat": lambda: self.spotify.repeat(state="track"),
                "shuffle": lambda: self.spotify.shuffle(state=True)
            }
            func = actions.get(action)
            if func:
                func()
        except Exception as e:
            print(f"⚠️ Error performing {action}: {e}")

    def add_to_queue(self, track_uri: str):
        self.spotify.add_to_queue(track_uri)
        print("✅ Added track to queue")

    def search_tracks(self, query: str):
        results = self.spotify.search(q=query, type="track", limit=10)
        return [
            f"{i + 1}. {t['name']} - {t['artists'][0]['name']} (spotify:track:{t['id']})"
            for i, t in enumerate(results["tracks"]["items"])
        ]


class AurafyUI:
    def __init__(self, root, spotify_client: SpotifyClient):
        self.root = root
        self.spotify = spotify_client
        self.repeat_on = False
        self.shuffle_on = False

        self.root.title("Aurafy by Param — Spotify Controller")
        self.root.geometry("1024x640")
        self.root.configure(bg="#111")

        self.track_label = tk.Label(root, text="", fg="white", bg="#111", font=("Segoe UI", 16))
        self.artist_label = tk.Label(root, text="", fg="#aaa", bg="#111", font=("Segoe UI", 13))
        self.album_art_label = tk.Label(root, bg="#111")

        self.track_label.pack(pady=10)
        self.artist_label.pack()
        self.album_art_label.pack(pady=30)

        self.create_controls()
        self.refresh_track_info()

    def create_controls(self):
        frame = tk.Frame(self.root, bg="#111")
        frame.pack(pady=20)

        buttons = [
            ("⏮", "prev"), ("▶", "play"), ("⏸", "pause"), ("⏭", "next"),
            ("🔁", "repeat"), ("🔀", "shuffle")
        ]

        for text, action in buttons:
            tk.Button(
                frame, text=text, width=5, font=("Segoe UI", 16),
                bg="#222", fg="white", relief="flat",
                command=lambda a=action: self.handle_action(a)
            ).pack(side="left", padx=5)

        # Search bar
        self.search_entry = tk.Entry(self.root, width=50, font=("Segoe UI", 12))
        self.search_entry.pack(pady=10)
        tk.Button(
            self.root, text="🔍 Search", command=self.search_songs,
            bg="#1db954", fg="white", font=("Segoe UI", 12, "bold")
        ).pack()

    def handle_action(self, action):
        if action in ["repeat", "shuffle"]:
            self.toggle_mode(action)
        else:
            self.spotify.control(action)
            Timer(1, self.refresh_track_info).start()

    def toggle_mode(self, mode):
        if mode == "repeat":
            self.repeat_on = not self.repeat_on
            self.spotify.spotify.repeat("track" if self.repeat_on else "off")
            print(f"Repeat: {'ON' if self.repeat_on else 'OFF'}")
        elif mode == "shuffle":
            self.shuffle_on = not self.shuffle_on
            self.spotify.spotify.shuffle(self.shuffle_on)
            print(f"Shuffle: {'ON' if self.shuffle_on else 'OFF'}")

    def refresh_track_info(self):
        track = self.spotify.get_current_track()
        if not track:
            self.track_label.config(text="No track playing")
            self.artist_label.config(text="")
            self.album_art_label.config(image="")
            return

        self.track_label.config(text=track["title"])
        self.artist_label.config(text=track["artist"])

        try:
            response = requests.get(track["album_art"])
            img = Image.open(BytesIO(response.content)).resize((400, 400))
            tk_img = ImageTk.PhotoImage(img)
            self.album_art_label.config(image=tk_img)
            self.album_art_label.image = tk_img
        except Exception:
            pass

    def search_songs(self):
        query = self.search_entry.get()
        results = self.spotify.search_tracks(query)
        print("\n🔍 Search Results:")
        for r in results:
            print(r)
        self.search_entry.delete(0, tk.END)


if __name__ == "__main__":
    creds = SpotifyCredentials(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET")
    )
    spotify_client = SpotifyClient(creds)
    root = tk.Tk()
    AurafyUI(root, spotify_client)
    root.mainloop()
