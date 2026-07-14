from dataclasses import dataclass
from typing import Optional


@dataclass
class Concert:
    artist: str
    event_name: str
    venue: str
    city: str
    country: str
    date: str
    time: Optional[str]
    ticket_url: Optional[str]
    bandsintown_url: str

    @classmethod
    def from_bandsintown(cls, data: dict, artist_name: str) -> "Concert":
        # Venue info
        venue = data.get("venue", {})
        venue_name = venue.get("name", "Unknown Venue")
        city = venue.get("city", "Unknown City")
        country = venue.get("country", "Unknown Country")
        region = venue.get("region", "")

        # Date/time — format: "2024-11-15T20:00:00"
        raw_datetime = data.get("datetime", "")
        if raw_datetime:
            parts = raw_datetime.split("T")
            date = parts[0]
            time = parts[1][:5] if len(parts) > 1 else None
        else:
            date = "TBA"
            time = None

        # Offers (ticket links)
        offers = data.get("offers", [])
        ticket_url = offers[0].get("url") if offers else None

        return cls(
            artist=artist_name,
            event_name=data.get("title") or f"{artist_name} in {city}",
            venue=venue_name,
            city=city,
            country=country,
            date=date,
            time=time,
            ticket_url=ticket_url,
            bandsintown_url=data.get("url", ""),
        )
