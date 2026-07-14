from typing import List, Optional
import requests
from ticketmaster.models import Concert
from config import TICKETMASTER_API_KEY, TICKETMASTER_BASE_URL


def search_concerts(
    artist_name: str,
    country_codes: List[str],
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[int] = None,
) -> List[Concert]:
    """
    Search Ticketmaster for concerts by artist name.

    Args:
        artist_name: Name of the artist to search for
        country_codes: List of ISO country codes (e.g. ['US', 'GB'])
        city: Optional city name (for display/filtering)
        lat: Optional latitude for radius search
        lng: Optional longitude for radius search
        radius_km: Optional search radius in kilometers

    Returns:
        List of Concert objects sorted by date
    """
    concerts = []

    for country_code in country_codes:
        params = {
            "apikey": TICKETMASTER_API_KEY,
            "keyword": artist_name,
            "countryCode": country_code,
            "classificationName": "music",
            "size": 20,
            "sort": "date,asc",
        }

        if lat is not None and lng is not None and radius_km is not None:
            params["latlong"] = f"{lat},{lng}"
            params["radius"] = str(radius_km)
            params["unit"] = "km"

        try:
            resp = requests.get(
                f"{TICKETMASTER_BASE_URL}/events.json",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            events = data.get("_embedded", {}).get("events", [])
            for event in events:
                concerts.append(Concert.from_ticketmaster(event, artist_name))

        except requests.exceptions.RequestException:
            # Skip failed country lookups silently; surface errors at UI layer if needed
            continue

    # Deduplicate by event name + date + venue
    seen = set()
    unique = []
    for c in concerts:
        key = (c.name, c.date, c.venue)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Sort by date
    unique.sort(key=lambda c: c.date)
    return unique


def geocode_city(city: str) -> Optional[tuple]:
    """
    Use Ticketmaster's suggest API to find lat/lng for a city.
    Falls back to None, None if not found.

    Returns:
        (lat, lng) tuple or (None, None)
    """
    try:
        resp = requests.get(
            f"{TICKETMASTER_BASE_URL}/suggest",
            params={
                "apikey": TICKETMASTER_API_KEY,
                "keyword": city,
                "resource": "venues",
                "size": 1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        venues = data.get("_embedded", {}).get("venues", [])
        if venues:
            loc = venues[0].get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            if lat and lng:
                return float(lat), float(lng)
    except Exception:
        pass
    return None, None
