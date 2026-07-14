from typing import List, Optional, Tuple
import questionary
from questionary import Style
from spotify.client import TIME_RANGE_LABELS

# Custom questionary style to match Rich's color scheme
STYLE = Style([
    ("qmark", "fg:#00ff87 bold"),
    ("question", "bold"),
    ("answer", "fg:#00bfff bold"),
    ("pointer", "fg:#00ff87 bold"),
    ("highlighted", "fg:#00ff87 bold"),
    ("selected", "fg:#00bfff"),
    ("separator", "fg:#6c6c6c"),
    ("instruction", "fg:#6c6c6c"),
])

# ISO country codes with display names
COUNTRIES = {
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


def ask_artist_source() -> str:
    """Ask whether to use top artists, followed artists, or both."""
    return questionary.select(
        "Which artists should we search concerts for?",
        choices=[
            questionary.Choice("Both top played & followed artists", value="both"),
            questionary.Choice("Top played artists only", value="top"),
            questionary.Choice("Followed artists only", value="followed"),
        ],
        style=STYLE,
    ).ask()


def ask_time_range() -> str:
    """Ask which Spotify time range to use for top artists."""
    choices = [
        questionary.Choice(label, value=key)
        for key, label in TIME_RANGE_LABELS.items()
    ]
    return questionary.select(
        "Which time period for your top artists?",
        choices=choices,
        style=STYLE,
    ).ask()


def ask_countries() -> List[str]:
    """Multi-select list of countries to search concerts in."""
    choices = [
        questionary.Choice(f"{name} ({code})", value=code)
        for code, name in sorted(COUNTRIES.items(), key=lambda x: x[1])
    ]
    selected = questionary.checkbox(
        "Select countries to search for concerts (space to select, enter to confirm):",
        choices=choices,
        style=STYLE,
    ).ask()
    return selected or []


def ask_radius_search() -> Tuple[Optional[str], Optional[int]]:
    """
    Optionally ask for a city + radius to narrow the search.
    Returns (city_name, radius_km) or (None, None) if skipped.
    """
    use_radius = questionary.confirm(
        "Also search within a radius of a specific city?",
        default=False,
        style=STYLE,
    ).ask()

    if not use_radius:
        return None, None

    city = questionary.text(
        "Enter city name:",
        style=STYLE,
    ).ask()

    radius_str = questionary.select(
        "Search radius:",
        choices=[
            questionary.Choice("25 km", value=25),
            questionary.Choice("50 km", value=50),
            questionary.Choice("100 km", value=100),
            questionary.Choice("200 km", value=200),
            questionary.Choice("500 km", value=500),
        ],
        style=STYLE,
    ).ask()

    return city, radius_str


def ask_main_menu() -> str:
    """Main menu after viewing results."""
    return questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("Search concerts again with different settings", value="search"),
            questionary.Choice("View my artists again", value="artists"),
            questionary.Choice("Exit", value="exit"),
        ],
        style=STYLE,
    ).ask()


def ask_continue() -> bool:
    """Ask if the user wants to continue."""
    return questionary.confirm("Continue?", default=True, style=STYLE).ask()
