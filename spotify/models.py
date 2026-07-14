from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Artist:
    id: str
    name: str
    genres: List[str]
    popularity: int
    url: str
    image_url: Optional[str] = None

    @classmethod
    def from_spotify(cls, data: dict) -> "Artist":
        images = data.get("images", [])
        image_url = images[0]["url"] if images else None
        return cls(
            id=data["id"],
            name=data["name"],
            genres=data.get("genres", []),
            popularity=data.get("popularity", 0),
            url=data.get("external_urls", {}).get("spotify", ""),
            image_url=image_url,
        )
