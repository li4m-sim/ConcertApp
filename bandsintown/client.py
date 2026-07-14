from typing import List, Optional
import requests
from bandsintown.models import Concert
from config import BANDSINTOWN_APP_ID

BASE_URL = "https://rest.bandsintown.com"


def get_artist_events(
    artist_name: str,
    country_codes: Optional[List[str]] = None,
) -> List[Concert]:
    """
    Fetch upcoming events for an artist from the Bandsintown API.

    Bandsintown does not support server-side country filtering, so we fetch
    all upcoming events and filter locally by country code.

    Args:
        artist_name: Name of the artist
        country_codes: Optional list of ISO 3166-1 alpha-2 country codes to filter by

    Returns:
        List of Concert objects
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/artists/{requests.utils.quote(artist_name)}/events",
            params={"app_id": BANDSINTOWN_APP_ID},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        # Bandsintown returns an error dict or a string "Not Found" on failure
        if not isinstance(data, list):
            return []

        concerts = [Concert.from_bandsintown(event, artist_name) for event in data]

        # Filter by country codes if provided
        if country_codes:
            # Bandsintown returns full country names, not codes
            # Build a set of lowercase names from the code list for comparison
            allowed_names = {
                _country_code_to_name(code).lower()
                for code in country_codes
            }
            concerts = [
                c for c in concerts
                if c.country.lower() in allowed_names
            ]

        return concerts

    except requests.exceptions.RequestException:
        return []


def search_concerts(
    artist_name: str,
    country_codes: List[str],
    city: Optional[str] = None,
    radius_km: Optional[int] = None,
) -> List[Concert]:
    """
    Search for concerts for an artist, filtered by countries and optionally city+radius.

    Args:
        artist_name: Artist name to search
        country_codes: ISO country codes to include
        city: Optional city name to filter by
        radius_km: Not used by Bandsintown API — city name match is used instead

    Returns:
        Filtered, sorted list of Concert objects
    """
    concerts = get_artist_events(artist_name, country_codes=country_codes)

    # Optional city filter (case-insensitive substring match)
    if city:
        city_lower = city.lower()
        concerts = [c for c in concerts if city_lower in c.city.lower()]

    concerts.sort(key=lambda c: c.date)
    return concerts


# --- Country code -> name mapping (subset matching Bandsintown responses) ---

_CODE_TO_NAME = {
    "AT": "Austria",
    "AU": "Australia",
    "BE": "Belgium",
    "BR": "Brazil",
    "CA": "Canada",
    "CH": "Switzerland",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Denmark",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GB": "United Kingdom",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "JP": "Japan",
    "MX": "Mexico",
    "NL": "Netherlands",
    "NO": "Norway",
    "NZ": "New Zealand",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SE": "Sweden",
    "TR": "Turkey",
    "US": "United States",
    "ZA": "South Africa",
}


def _country_code_to_name(code: str) -> str:
    return _CODE_TO_NAME.get(code.upper(), code)
