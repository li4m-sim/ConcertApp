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
    """
    2-step country selection:
    Step 1 — choose a continent, all countries, or pick specific ones.
    Step 2 — if picking specific: autocomplete search loop.
    """
    # Build step 1 choices
    continent_choices = [
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

    if scope == "all":
        return list(COUNTRIES.keys())

    if scope.startswith("continent:"):
        continent_name = scope.split(":", 1)[1]
        return list(CONTINENTS[continent_name].keys())

    # "specific" — autocomplete loop
    return _ask_specific_countries()


def _ask_specific_countries() -> List[str]:
    """
    Autocomplete loop — user types to search for a country,
    selects it, then optionally adds more.
    """
    # Build autocomplete list: "Germany (DE)", sorted by name
    all_options = sorted(
        [f"{name} ({code})" for code, name in COUNTRIES.items()],
        key=lambda x: x.lower(),
    )

    selected_codes = []
    selected_labels = []

    while True:
        # Show already selected countries
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

        # Empty input or cancelled — done
        if not answer:
            break

        # Parse "Germany (DE)" -> code "DE"
        if "(" in answer and answer.endswith(")"):
            code = answer.split("(")[-1].rstrip(")")
            name = answer.split(" (")[0]
            if code not in selected_codes:
                selected_codes.append(code)
                selected_labels.append(name)

        # Ask if they want to add more
        add_more = questionary.confirm(
            "Add another country?",
            default=True,
            style=STYLE,
        ).ask()

        if not add_more:
            break

    return selected_codes


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
