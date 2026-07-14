import os
from dotenv import load_dotenv

load_dotenv()

# Spotify
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
SPOTIFY_CACHE_PATH = os.path.expanduser("~/.cache/spotifyapp")

SPOTIFY_SCOPES = [
    "user-top-read",
    "user-follow-read",
]

# Bandsintown — no registration required, just pick a name for your app
BANDSINTOWN_APP_ID = os.getenv("BANDSINTOWN_APP_ID", "spotifyconcertfinder")

# App defaults
DEFAULT_TOP_ARTISTS_LIMIT = 20
DEFAULT_FOLLOWED_ARTISTS_LIMIT = 50
