from typing import List, Optional, Tuple, Dict
from datetime import date
import math
import requests
from bandsintown.models import Concert
from config import BANDSINTOWN_APP_ID
from ui.menus import COUNTRIES

BASE_URL = "https://rest.bandsintown.com"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# In-memory cache for geocoded cities within a single run
_geocode_cache: Dict[str, Optional[Tuple[float, float]]] = {}


def _geocode(city: str) -> Optional[Tuple[float, float]]:
    """
    Convert a city name to (latitude, longitude) using the Nominatim API.
    Returns None if the city cannot be found.
    Results are cached for the lifetime of the process.
    """
    key = city.strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "SpotifyApp/1.0 (concert-radius-search)"},
            timeout=10,
        )
        if resp.ok:
            results = resp.json()
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                _geocode_cache[key] = (lat, lon)
                return (lat, lon)
    except Exception:
        pass

    _geocode_cache[key] = None
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two (lat, lon) points."""
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def get_artist_events(
    artist_name: str,
    country_codes: Optional[List[str]] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    debug: bool = False,
) -> List[Concert]:
    """
    Fetch upcoming events for an artist from the Bandsintown API.

    Filters locally by country code and date range.

    Args:
        artist_name: Name of the artist
        country_codes: ISO country codes to filter by. Pass [] or None for all locations.
        date_from: Optional start date filter (inclusive)
        date_to: Optional end date filter (inclusive)
        debug: If True, print API errors and filter stats to the terminal

    Returns:
        List of Concert objects
    """
    from ui import display

    try:
        resp = requests.get(
            f"{BASE_URL}/artists/{requests.utils.quote(artist_name)}/events",
            params={"app_id": BANDSINTOWN_APP_ID},
            timeout=10,
        )

        if not resp.ok:
            if debug:
                display.print_api_error(
                    artist_name=artist_name,
                    status_code=resp.status_code,
                    detail=resp.reason or "Unknown error",
                    app_id=BANDSINTOWN_APP_ID,
                )
            return []

        data = resp.json()

        if not isinstance(data, list):
            if debug:
                display.print_api_error(
                    artist_name=artist_name,
                    status_code=resp.status_code,
                    detail=f"Unexpected response format: {str(data)[:120]}",
                    app_id=BANDSINTOWN_APP_ID,
                )
            return []

        all_concerts = [Concert.from_bandsintown(event, artist_name) for event in data]

        # Country filter — skip if empty (all locations)
        if country_codes:
            allowed_names = {
                _country_code_to_name(code).lower()
                for code in country_codes
            }
            filtered = [
                c for c in all_concerts
                if c.country.lower() in allowed_names
            ]
        else:
            filtered = all_concerts

        # Date range filter
        if date_from:
            filtered = [c for c in filtered if c.date >= str(date_from)]
        if date_to:
            filtered = [c for c in filtered if c.date <= str(date_to)]

        if debug:
            country_names = (
                [_country_code_to_name(c) for c in country_codes]
                if country_codes
                else ["all locations"]
            )
            display.print_debug_info(
                artist_name=artist_name,
                total_events=len(all_concerts),
                filtered_events=len(filtered),
                country_names=country_names,
            )

        return filtered

    except requests.exceptions.ConnectionError:
        if debug:
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail="Connection error — check your internet connection.",
                app_id=BANDSINTOWN_APP_ID,
            )
        return []
    except requests.exceptions.Timeout:
        if debug:
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail="Request timed out after 10 seconds.",
                app_id=BANDSINTOWN_APP_ID,
            )
        return []
    except requests.exceptions.RequestException as e:
        if debug:
            display.print_api_error(
                artist_name=artist_name,
                status_code=0,
                detail=str(e),
                app_id=BANDSINTOWN_APP_ID,
            )
        return []


def search_concerts(
    artist_name: str,
    country_codes: List[str],
    city: Optional[str] = None,
    radius_km: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    debug: bool = False,
) -> List[Concert]:
    """
    Search for concerts for an artist, filtered by countries, date range, and optionally
    a city radius (geocoded via Nominatim).

    Args:
        artist_name: Artist name to search
        country_codes: ISO country codes to include. Empty list = all locations.
        city: Optional reference city for radius filtering
        radius_km: Radius in km around city. Requires city to be set.
        date_from: Optional start date filter (inclusive)
        date_to: Optional end date filter (inclusive)
        debug: If True, surface API errors and filter stats

    Returns:
        Filtered, sorted list of Concert objects
    """
    from ui import display

    concerts = get_artist_events(
        artist_name,
        country_codes=country_codes,
        date_from=date_from,
        date_to=date_to,
        debug=debug,
    )

    # Radius filter — geocode reference city, then filter by distance
    if city and radius_km:
        ref_coords = _geocode(city)
        if ref_coords is None:
            if debug:
                display.print_info(f"[DEV] Could not geocode reference city: {city!r}")
        else:
            ref_lat, ref_lon = ref_coords
            filtered = []
            for c in concerts:
                concert_city_str = f"{c.city}, {c.country}"
                concert_coords = _geocode(concert_city_str)
                if concert_coords is None:
                    concert_coords = _geocode(c.city)
                if concert_coords is not None:
                    dist = _haversine_km(ref_lat, ref_lon, concert_coords[0], concert_coords[1])
                    if dist <= radius_km:
                        filtered.append(c)
                elif debug:
                    display.print_info(f"[DEV] Could not geocode concert city: {concert_city_str!r}")
            concerts = filtered
    elif city:
        # Fallback: plain substring match if no radius given
        city_lower = city.lower()
        concerts = [c for c in concerts if city_lower in c.city.lower()]

    concerts.sort(key=lambda c: c.date)
    return concerts


def _country_code_to_name(code: str) -> str:
    return COUNTRIES.get(code.upper(), code)
