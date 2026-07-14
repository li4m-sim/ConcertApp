from dataclasses import dataclass
from typing import Optional


@dataclass
class Concert:
    name: str
    artist: str
    venue: str
    city: str
    country: str
    date: str
    time: Optional[str]
    url: str
    min_price: Optional[str] = None
    max_price: Optional[str] = None

    @classmethod
    def from_ticketmaster(cls, data: dict, artist_name: str) -> "Concert":
        # Venue info
        venues = data.get("_embedded", {}).get("venues", [{}])
        venue = venues[0] if venues else {}
        venue_name = venue.get("name", "Unknown Venue")
        city = venue.get("city", {}).get("name", "Unknown City")
        country = venue.get("country", {}).get("name", "Unknown Country")

        # Date/time
        dates = data.get("dates", {}).get("start", {})
        date = dates.get("localDate", "TBA")
        time = dates.get("localTime")
        if time:
            # Format HH:MM:SS -> HH:MM
            time = time[:5]

        # Price ranges
        price_ranges = data.get("priceRanges", [])
        min_price = None
        max_price = None
        if price_ranges:
            pr = price_ranges[0]
            currency = pr.get("currency", "")
            min_val = pr.get("min")
            max_val = pr.get("max")
            if min_val is not None:
                min_price = f"{min_val:.0f} {currency}"
            if max_val is not None:
                max_price = f"{max_val:.0f} {currency}"

        return cls(
            name=data.get("name", artist_name),
            artist=artist_name,
            venue=venue_name,
            city=city,
            country=country,
            date=date,
            time=time,
            url=data.get("url", ""),
            min_price=min_price,
            max_price=max_price,
        )
