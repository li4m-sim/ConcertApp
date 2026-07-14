from typing import List, Optional, Tuple, TYPE_CHECKING
from datetime import date, timedelta
import calendar
import questionary
from questionary import Style
from spotify.client import TIME_RANGE_LABELS

if TYPE_CHECKING:
    import spotipy
    from spotify.models import Artist

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

# Countries grouped by continent
CONTINENTS = {
    "Europe": {
        "AL": "Albania",
        "AD": "Andorra",
        "AT": "Austria",
        "BY": "Belarus",
        "BE": "Belgium",
        "BA": "Bosnia and Herzegovina",
        "BG": "Bulgaria",
        "HR": "Croatia",
        "CY": "Cyprus",
        "CZ": "Czech Republic",
        "DK": "Denmark",
        "EE": "Estonia",
        "FI": "Finland",
        "FR": "France",
        "DE": "Germany",
        "GR": "Greece",
        "HU": "Hungary",
        "IS": "Iceland",
        "IE": "Ireland",
        "IT": "Italy",
        "XK": "Kosovo",
        "LV": "Latvia",
        "LI": "Liechtenstein",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "MT": "Malta",
        "MD": "Moldova",
        "MC": "Monaco",
        "ME": "Montenegro",
        "NL": "Netherlands",
        "MK": "North Macedonia",
        "NO": "Norway",
        "PL": "Poland",
        "PT": "Portugal",
        "RO": "Romania",
        "RU": "Russia",
        "SM": "San Marino",
        "RS": "Serbia",
        "SK": "Slovakia",
        "SI": "Slovenia",
        "ES": "Spain",
        "SE": "Sweden",
        "CH": "Switzerland",
        "UA": "Ukraine",
        "GB": "United Kingdom",
    },
    "North America": {
        "CA": "Canada",
        "CR": "Costa Rica",
        "CU": "Cuba",
        "DO": "Dominican Republic",
        "GT": "Guatemala",
        "HN": "Honduras",
        "JM": "Jamaica",
        "MX": "Mexico",
        "PA": "Panama",
        "PR": "Puerto Rico",
        "TT": "Trinidad and Tobago",
        "US": "United States",
    },
    "South America": {
        "AR": "Argentina",
        "BO": "Bolivia",
        "BR": "Brazil",
        "CL": "Chile",
        "CO": "Colombia",
        "EC": "Ecuador",
        "PY": "Paraguay",
        "PE": "Peru",
        "UY": "Uruguay",
        "VE": "Venezuela",
    },
    "Asia": {
        "CN": "China",
        "HK": "Hong Kong",
        "IN": "India",
        "ID": "Indonesia",
        "JP": "Japan",
        "KZ": "Kazakhstan",
        "MY": "Malaysia",
        "MN": "Mongolia",
        "PH": "Philippines",
        "SG": "Singapore",
        "KR": "South Korea",
        "TW": "Taiwan",
        "TH": "Thailand",
        "VN": "Vietnam",
    },
    "Middle East": {
        "BH": "Bahrain",
        "IL": "Israel",
        "JO": "Jordan",
        "KW": "Kuwait",
        "LB": "Lebanon",
        "OM": "Oman",
        "QA": "Qatar",
        "SA": "Saudi Arabia",
        "TR": "Turkey",
        "AE": "United Arab Emirates",
    },
    "Oceania": {
        "AU": "Australia",
        "FJ": "Fiji",
        "NZ": "New Zealand",
    },
    "Africa": {
        "DZ": "Algeria",
        "EG": "Egypt",
        "ET": "Ethiopia",
        "GH": "Ghana",
        "KE": "Kenya",
        "MA": "Morocco",
        "NG": "Nigeria",
        "SN": "Senegal",
        "ZA": "South Africa",
        "TN": "Tunisia",
        "UG": "Uganda",
    },
}

# Flat dict of all countries for lookup elsewhere in the app
COUNTRIES = {
    code: name
    for region in CONTINENTS.values()
    for code, name in region.items()
}

# Reverse lookup: lowercase name -> code
_NAME_TO_CODE = {name.lower(): code for code, name in COUNTRIES.items()}


# ---------------------------------------------------------------------------
# Artist source selection
# ---------------------------------------------------------------------------

def ask_artist_sources() -> List[str]:
    """
    Multi-select: which sources should be included?
    Returns a list of selected source keys: 'top', 'followed', 'searched'
    """
    choices = [
        questionary.Choice("My top played artists", value="top"),
        questionary.Choice("My followed artists", value="followed"),
        questionary.Choice("Search for specific artists", value="searched"),
    ]
    selected = questionary.checkbox(
        "Which artist sources do you want to include? (space to select, enter to confirm)",
        choices=choices,
        style=STYLE,
    ).ask()
    return selected or []


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


def ask_specific_artists(sp: "spotipy.Spotify") -> List["Artist"]:
    """
    Autocomplete artist search loop using the Spotify search API.
    User types a query, picks from results, optionally adds more.
    Returns a list of Artist objects with source='searched'.
    """
    from spotify.client import search_artists

    selected: List["Artist"] = []

    while True:
        selected_names = [a.name for a in selected]
        if selected_names:
            prompt = f"Search for another artist (selected: {', '.join(selected_names)}):"
        else:
            prompt = "Search for an artist:"

        query = questionary.text(
            prompt,
            style=STYLE,
        ).ask()

        if not query or not query.strip():
            break

        results = search_artists(sp, query.strip())
        if not results:
            print("  No results found, try again.")
            continue

        # Let user pick from search results
        already_ids = {a.id for a in selected}
        choices = [
            questionary.Choice(
                f"{a.name}" + (f" — {', '.join(a.genres[:2])}" if a.genres else ""),
                value=a,
            )
            for a in results
            if a.id not in already_ids
        ]
        choices.append(questionary.Choice("[ Cancel / skip this search ]", value=None))

        pick = questionary.select(
            "Select an artist:",
            choices=choices,
            style=STYLE,
        ).ask()

        if pick is not None and hasattr(pick, "id"):
            selected.append(pick)

        add_more = questionary.confirm(
            "Search for another artist?",
            default=True,
            style=STYLE,
        ).ask()

        if not add_more:
            break

    return selected


def ask_no_artists_found() -> str:
    """
    Ask what to do when no artists were found/selected.
    Returns 'retry' or 'exit'.
    """
    return questionary.select(
        "No artists selected. What would you like to do?",
        choices=[
            questionary.Choice("Try again", value="retry"),
            questionary.Choice("Exit", value="exit"),
        ],
        style=STYLE,
    ).ask()


# ---------------------------------------------------------------------------
# Artist review / editing
# ---------------------------------------------------------------------------

def ask_review_artists(artists: List["Artist"]) -> str:
    """
    Show a summary of the current artist list and ask what to do next.
    Returns: 'continue', 'remove', 'add', 'restart'
    """
    count = len(artists)
    return questionary.select(
        f"Your artist list has {count} artist(s). What would you like to do?",
        choices=[
            questionary.Choice("Continue with these artists", value="continue"),
            questionary.Choice("Remove specific artists", value="remove"),
            questionary.Choice("Add more artists (search)", value="add"),
            questionary.Choice("Start over", value="restart"),
        ],
        style=STYLE,
    ).ask()


def ask_remove_artists(artists: List["Artist"]) -> List["Artist"]:
    """
    Let the user remove artists from the current list.
    - If <=20 artists: straight to checkbox.
    - If >20: offer checkbox or search-to-remove.
    Returns the updated list of artists to KEEP.
    """
    if len(artists) > 20:
        method = questionary.select(
            "How would you like to remove artists?",
            choices=[
                questionary.Choice("Uncheck from full list", value="checkbox"),
                questionary.Choice("Search by name", value="search"),
            ],
            style=STYLE,
        ).ask()
    else:
        method = "checkbox"

    if method == "checkbox":
        choices = [
            questionary.Choice(
                f"{a.name}  [{a.source}]",
                value=a,
                checked=True,  # all checked (kept) by default
            )
            for a in artists
        ]
        keep = questionary.checkbox(
            "Uncheck artists to remove them (enter to confirm):",
            choices=choices,
            style=STYLE,
        ).ask()
        return keep if keep is not None else artists

    else:
        # Search-to-remove loop
        remaining = list(artists)
        while True:
            query = questionary.text(
                "Type artist name to remove (leave blank to finish):",
                style=STYLE,
            ).ask()

            if not query or not query.strip():
                break

            query_lower = query.strip().lower()
            matches = [a for a in remaining if query_lower in a.name.lower()]

            if not matches:
                print("  No matching artists found.")
                continue

            choices = [
                questionary.Choice(f"{a.name}  [{a.source}]", value=a)
                for a in matches
            ]
            choices.append(questionary.Choice("[ Cancel ]", value=None))

            to_remove = questionary.select(
                "Select artist to remove:",
                choices=choices,
                style=STYLE,
            ).ask()

            if to_remove is not None:
                remaining = [a for a in remaining if a.id != to_remove.id]
                print(f"  Removed: {to_remove.name}")

            cont = questionary.confirm(
                "Remove another artist?",
                default=True,
                style=STYLE,
            ).ask()
            if not cont:
                break

        return remaining


# ---------------------------------------------------------------------------
# Country selection
# ---------------------------------------------------------------------------

def ask_countries() -> List[str]:
    """
    2-step country selection:
    Step 1 — choose all locations, a continent, all countries, or specific ones.
    Step 2 — if picking specific: autocomplete search loop.
    Returns [] for "all locations" (no country filter).
    """
    continent_choices = [
        questionary.Choice("All locations (no country filter)", value="all_locations"),
    ]
    continent_choices += [
        questionary.Choice(f"All of {continent}", value=f"continent:{continent}")
        for continent in CONTINENTS.keys()
    ]
    continent_choices.append(questionary.Choice("Pick specific countries", value="specific"))
    continent_choices.append(questionary.Choice("Select all countries", value="all"))

    scope = questionary.select(
        "Which countries should we search for concerts in?",
        choices=continent_choices,
        style=STYLE,
    ).ask()

    if scope is None:
        return []

    if scope == "all_locations":
        return []

    if scope == "all":
        return list(COUNTRIES.keys())

    if scope.startswith("continent:"):
        continent_name = scope.split(":", 1)[1]
        return list(CONTINENTS[continent_name].keys())

    return _ask_specific_countries()


def _ask_specific_countries() -> List[str]:
    """
    Autocomplete loop — user types to search for a country,
    selects it, then optionally adds more.
    """
    all_options = sorted(
        [f"{name} ({code})" for code, name in COUNTRIES.items()],
        key=lambda x: x.lower(),
    )

    selected_codes = []
    selected_labels = []

    while True:
        if selected_labels:
            prompt = f"Add another country? (selected: {', '.join(selected_labels)})"
        else:
            prompt = "Type to search for a country:"

        answer = questionary.autocomplete(
            prompt,
            choices=all_options,
            style=STYLE,
            validate=lambda val: val in all_options or val == "" or "Type a country name to search",
            ignore_case=True,
        ).ask()

        if not answer:
            break

        if "(" in answer and answer.endswith(")"):
            code = answer.split("(")[-1].rstrip(")")
            name = answer.split(" (")[0]
            if code not in selected_codes:
                selected_codes.append(code)
                selected_labels.append(name)

        add_more = questionary.confirm(
            "Add another country?",
            default=True,
            style=STYLE,
        ).ask()

        if not add_more:
            break

    return selected_codes


# ---------------------------------------------------------------------------
# Date range filter
# ---------------------------------------------------------------------------

def ask_date_range() -> Tuple[Optional[date], Optional[date]]:
    """
    Ask how far ahead to search for concerts.
    Returns (date_from, date_to) — either or both may be None (no limit).
    """
    today = date.today()

    preset = questionary.select(
        "How far ahead should we search for concerts?",
        choices=[
            questionary.Choice("No limit (all upcoming events)", value="none"),
            questionary.Choice("Next 1 month", value=1),
            questionary.Choice("Next 3 months", value=3),
            questionary.Choice("Next 6 months", value=6),
            questionary.Choice("Next 12 months", value=12),
            questionary.Choice("Custom range", value="custom"),
        ],
        style=STYLE,
    ).ask()

    if preset is None or preset == "none":
        return None, None

    if preset == "custom":
        return _ask_custom_date_range(today)

    # Preset month offsets
    date_from = today
    date_to = _add_months(today, preset)
    return date_from, date_to


def _ask_custom_date_range(today: date) -> Tuple[Optional[date], Optional[date]]:
    """Let the user pick a from/to month+year using select menus."""
    months = [
        questionary.Choice(calendar.month_name[m], value=m)
        for m in range(1, 13)
    ]

    # Offer years: current year + next 2
    years = [
        questionary.Choice(str(y), value=y)
        for y in range(today.year, today.year + 3)
    ]

    # From
    from_month = questionary.select("From month:", choices=months, style=STYLE).ask()
    from_year = questionary.select("From year:", choices=years, style=STYLE).ask()

    if from_month is None or from_year is None:
        return None, None

    date_from = date(from_year, from_month, 1)

    # To
    to_month = questionary.select("To month:", choices=months, style=STYLE).ask()
    to_year = questionary.select("To year:", choices=years, style=STYLE).ask()

    if to_month is None or to_year is None:
        return date_from, None

    # Last day of the selected to-month
    last_day = calendar.monthrange(to_year, to_month)[1]
    date_to = date(to_year, to_month, last_day)

    return date_from, date_to


def _add_months(d: date, months: int) -> date:
    """Add a number of months to a date, clamping to the last day of the month."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return date(year, month, day)


# ---------------------------------------------------------------------------
# Radius / city search
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Run mode
# ---------------------------------------------------------------------------

def ask_run_mode() -> bool:
    """
    Ask the user whether to run in normal or developer mode.
    If developer mode is selected, prompt for the DEV_PASSWORD from .env.
    Returns True if developer mode was granted, False otherwise.
    """
    from config import DEV_PASSWORD

    choice = questionary.select(
        "Select run mode:",
        choices=[
            questionary.Choice("Normal mode", value="normal"),
            questionary.Choice(
                "Developer mode  (shows API errors and debug info)",
                value="developer",
            ),
        ],
        style=STYLE,
    ).ask()

    if choice != "developer":
        return False

    # If no password is configured, deny access
    if not DEV_PASSWORD:
        print("  Developer mode is not configured (DEV_PASSWORD not set in .env).")
        return False

    # Prompt up to 3 times
    for attempt in range(1, 4):
        password = questionary.password(
            f"Enter developer password (attempt {attempt}/3):",
            style=STYLE,
        ).ask()

        if password is None:
            return False

        if password == DEV_PASSWORD:
            return True

        print(f"  Incorrect password.")

    print("  Too many failed attempts. Switching to normal mode.")
    return False


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def ask_main_menu() -> str:
    """Main menu after viewing results."""
    return questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("Search concerts for current artists", value="search"),
            questionary.Choice("Change artist selection", value="change_artists"),
            questionary.Choice("View my artists", value="artists"),
            questionary.Choice("Logout & switch account", value="logout"),
            questionary.Choice("Exit", value="exit"),
        ],
        style=STYLE,
    ).ask()


def ask_continue() -> bool:
    """Ask if the user wants to continue."""
    return questionary.confirm("Continue?", default=True, style=STYLE).ask()
