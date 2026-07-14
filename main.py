import sys
from typing import List

from rich.console import Console

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from auth.spotify_auth import create_spotify_client, get_current_user
from spotify.client import get_top_artists, get_followed_artists, TIME_RANGE_LABELS
from spotify.models import Artist
from bandsintown.client import search_concerts
from bandsintown.models import Concert
from ui import display
from ui import menus

console = Console()


def check_credentials() -> bool:
    """Verify that required Spotify credentials are present."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        display.print_no_credentials_warning()
        return False
    return True


def fetch_artists(sp, source: str, time_range: str) -> List[Artist]:
    """Fetch artists based on the selected source."""
    top_artists = []
    followed_artists = []

    if source in ("top", "both"):
        display.print_info(f"Fetching your top artists ({TIME_RANGE_LABELS[time_range]})...")
        top_artists = get_top_artists(sp, time_range=time_range)

    if source in ("followed", "both"):
        display.print_info("Fetching your followed artists...")
        followed_artists = get_followed_artists(sp)

    return top_artists, followed_artists


def find_concerts(
    artists: List[Artist],
    country_codes: List[str],
    city: str,
    radius_km: int,
) -> List[Concert]:
    """Search Bandsintown for concerts for all artists."""
    all_concerts = []
    for artist in artists:
        display.print_searching(artist.name)
        concerts = search_concerts(
            artist_name=artist.name,
            country_codes=country_codes,
            city=city,
        )
        all_concerts.extend(concerts)

    # Clear the searching line
    console.print(" " * 60, end="\r")

    # Deduplicate across artists
    seen = set()
    unique = []
    for c in all_concerts:
        key = (c.event_name, c.date, c.venue)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    unique.sort(key=lambda c: c.date)
    return unique


def run_concert_search(artists: List[Artist]) -> None:
    """Run the concert search flow for a given list of artists."""
    if not artists:
        display.print_info("No artists to search for.")
        return

    # Ask for countries
    country_codes = menus.ask_countries()
    if not country_codes:
        display.print_info("No countries selected. Skipping concert search.")
        return

    # Ask for optional city+radius
    city, radius_km = menus.ask_radius_search()

    # Search
    display.print_section("Searching for Concerts")
    concerts = find_concerts(artists, country_codes, city, radius_km)

    # Build title
    country_names = [menus.COUNTRIES.get(c, c) for c in country_codes]
    title_parts = [", ".join(country_names)]
    if city and radius_km:
        title_parts.append(f"within {radius_km}km of {city}")
    title = "Upcoming Concerts — " + " | ".join(title_parts)

    display.print_concerts_table(concerts, title)


def main() -> None:
    console.clear()

    # 1. Check credentials
    if not check_credentials():
        sys.exit(1)

    # 2. Authenticate with Spotify
    display.print_info("Connecting to Spotify...")
    try:
        sp = create_spotify_client()
        user = get_current_user(sp)
    except Exception as e:
        display.print_error(f"Spotify authentication failed: {e}")
        sys.exit(1)

    # 3. Welcome banner
    display.print_welcome(
        username=user.get("id", ""),
        display_name=user.get("display_name", ""),
    )

    # 4. Choose artist source
    source = menus.ask_artist_source()
    if source is None:
        sys.exit(0)

    # 5. Time range (only needed for top artists)
    time_range = "medium_term"
    if source in ("top", "both"):
        time_range = menus.ask_time_range()
        if time_range is None:
            sys.exit(0)

    # 6. Fetch artists
    top_artists, followed_artists = fetch_artists(sp, source, time_range)

    # 7. Display artists
    if top_artists:
        display.print_section("Your Top Artists")
        display.print_artists_table(
            top_artists,
            title=f"Top Artists — {TIME_RANGE_LABELS[time_range]}",
        )

    if followed_artists:
        display.print_section("Artists You Follow")
        display.print_artists_table(followed_artists, title="Followed Artists")

    # 8. Combine unique artists for concert search
    all_artist_ids = set()
    combined = []
    for artist in top_artists + followed_artists:
        if artist.id not in all_artist_ids:
            all_artist_ids.add(artist.id)
            combined.append(artist)

    # 9. Main loop
    while True:
        action = menus.ask_main_menu()
        if action is None or action == "exit":
            console.print("\n[bold green]Goodbye![/bold green]")
            break
        elif action == "search":
            run_concert_search(combined)
        elif action == "artists":
            if top_artists:
                display.print_artists_table(
                    top_artists,
                    title=f"Top Artists — {TIME_RANGE_LABELS[time_range]}",
                )
            if followed_artists:
                display.print_artists_table(followed_artists, title="Followed Artists")


if __name__ == "__main__":
    main()
