import sys
from datetime import date
from typing import List, Optional

import spotipy
from rich.console import Console

import config
import updater
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from auth.spotify_auth import create_spotify_client, get_current_user, logout
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


def manage_artists(sp: spotipy.Spotify) -> List[Artist]:
    """
    Full artist management flow:
    1. Multi-select sources (top / followed / search)
    2. Configure each source
    3. Review & edit the combined list (remove, add, restart)
    Returns the final confirmed list of artists.
    """
    while True:
        # Step 1 — choose sources
        sources = menus.ask_artist_sources()
        if not sources:
            display.print_info("No sources selected.")
            continue

        combined: List[Artist] = []

        # Step 2 — fetch / collect each source
        if "top" in sources:
            time_range = menus.ask_time_range()
            if time_range is None:
                continue
            display.print_info(f"Fetching your top artists ({TIME_RANGE_LABELS[time_range]})...")
            combined.extend(get_top_artists(sp, time_range=time_range))

        if "followed" in sources:
            display.print_info("Fetching your followed artists...")
            combined.extend(get_followed_artists(sp))

        if "searched" in sources:
            searched = menus.ask_specific_artists(sp)
            combined.extend([a for a in (searched or []) if hasattr(a, "id")])

        # Deduplicate by Spotify ID (keep first occurrence, preserve source)
        seen_ids = set()
        unique: List[Artist] = []
        for artist in combined:
            if artist.id not in seen_ids:
                seen_ids.add(artist.id)
                unique.append(artist)
        combined = unique

        if not combined:
            action = menus.ask_no_artists_found()
            if action == "exit":
                console.print("\n[bold green]Goodbye![/bold green]")
                sys.exit(0)
            continue

        # Step 3 — review / edit loop
        while True:
            display.print_section("Your Artist List")
            display.print_artists_table(combined, title=f"Artists ({len(combined)})")

            action = menus.ask_review_artists(combined)

            if action is None or action == "continue":
                return combined

            elif action == "remove":
                combined = menus.ask_remove_artists(combined)
                if not combined:
                    display.print_info("All artists removed. Starting over.")
                    break  # back to source selection

            elif action == "add":
                added = menus.ask_specific_artists(sp)
                for artist in (added or []):
                    if hasattr(artist, "id") and artist.id not in {a.id for a in combined}:
                        combined.append(artist)

            elif action == "restart":
                break  # back to source selection


def find_concerts(
    artists: List[Artist],
    country_codes: List[str],
    city: Optional[str],
    radius_km: Optional[int],
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[Concert]:
    """Search Bandsintown for concerts for all artists."""
    all_concerts = []
    for artist in artists:
        display.print_searching(artist.name)
        concerts = search_concerts(
            artist_name=artist.name,
            country_codes=country_codes,
            city=city,
            date_from=date_from,
            date_to=date_to,
            debug=config.DEBUG_MODE,
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

    country_codes = menus.ask_countries()

    city, radius_km = menus.ask_radius_search()

    date_from, date_to = menus.ask_date_range()

    display.print_section("Searching for Concerts")
    concerts = find_concerts(artists, country_codes, city, radius_km, date_from, date_to)

    # Build title
    if country_codes:
        country_names = [menus.COUNTRIES.get(c, c) for c in country_codes]
        location_str = ", ".join(country_names)
    else:
        location_str = "All locations"

    title_parts = [location_str]
    if city and radius_km:
        title_parts.append(f"within {radius_km}km of {city}")
    if date_from and date_to:
        title_parts.append(f"{date_from.strftime('%b %Y')} – {date_to.strftime('%b %Y')}")
    elif date_from:
        title_parts.append(f"from {date_from.strftime('%b %Y')}")
    elif date_to:
        title_parts.append(f"until {date_to.strftime('%b %Y')}")

    title = "Upcoming Concerts — " + " | ".join(title_parts)

    display.print_concerts_table(concerts, title)


def main() -> None:
    # Check for updates before anything else — silently skips if not due or on any error
    updater.check_and_update()

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

    # 3. Ask run mode (before welcome banner so banner reflects choice)
    config.DEBUG_MODE = menus.ask_run_mode()

    # 4. Welcome banner
    display.print_welcome(
        username=user.get("id", ""),
        display_name=user.get("display_name", ""),
        dev_mode=config.DEBUG_MODE,
    )

    if config.DEBUG_MODE:
        from config import BANDSINTOWN_APP_ID
        display.print_info(f"[DEV] BANDSINTOWN_APP_ID = \"{BANDSINTOWN_APP_ID}\"")
        display.print_info(f"[DEV] Spotify user ID    = \"{user.get('id', '')}\"")

    # 5. Artist management (initial)
    combined = manage_artists(sp)

    # 6. Main loop
    while True:
        action = menus.ask_main_menu()

        if action is None or action == "exit":
            console.print("\n[bold green]Goodbye![/bold green]")
            break

        elif action == "search":
            run_concert_search(combined)

        elif action == "change_artists":
            combined = manage_artists(sp)

        elif action == "logout":
            display.print_info("Logging out...")
            logout()
            display.print_info("Token cleared. Opening browser for fresh login...")
            try:
                sp = create_spotify_client()
                user = get_current_user(sp)
            except Exception as e:
                display.print_error(f"Spotify authentication failed: {e}")
                sys.exit(1)
            display.print_welcome(
                username=user.get("id", ""),
                display_name=user.get("display_name", ""),
                dev_mode=config.DEBUG_MODE,
            )
            combined = manage_artists(sp)

        elif action == "artists":
            display.print_section("Your Artist List")
            display.print_artists_table(combined, title=f"Artists ({len(combined)})")


if __name__ == "__main__":
    main()
