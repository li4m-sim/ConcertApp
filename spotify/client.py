from typing import List
import spotipy
from spotify.models import Artist
from config import DEFAULT_TOP_ARTISTS_LIMIT, DEFAULT_FOLLOWED_ARTISTS_LIMIT


TIME_RANGE_LABELS = {
    "short_term": "Last 4 weeks",
    "medium_term": "Last 6 months",
    "long_term": "All time",
}


def get_top_artists(sp: spotipy.Spotify, time_range: str = "medium_term") -> List[Artist]:
    """
    Fetch the current user's top artists from Spotify.

    Args:
        sp: Authenticated Spotipy client
        time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (all time)

    Returns:
        List of Artist objects
    """
    results = sp.current_user_top_artists(
        limit=DEFAULT_TOP_ARTISTS_LIMIT,
        time_range=time_range,
    )
    return [Artist.from_spotify(item) for item in results.get("items", [])]


def get_followed_artists(sp: spotipy.Spotify) -> List[Artist]:
    """
    Fetch all artists the current user follows on Spotify.

    Returns:
        List of Artist objects
    """
    artists = []
    after = None

    while True:
        results = sp.current_user_followed_artists(
            limit=50,
            after=after,
        )
        items = results.get("artists", {}).get("items", [])
        artists.extend([Artist.from_spotify(item) for item in items])

        cursor = results.get("artists", {}).get("cursors", {})
        after = cursor.get("after")
        if not after or len(items) == 0:
            break

    return artists[:DEFAULT_FOLLOWED_ARTISTS_LIMIT]
