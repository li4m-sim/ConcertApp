from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from spotify.models import Artist
from bandsintown.models import Concert

console = Console()


def print_welcome(username: str, display_name: str) -> None:
    """Print a welcome banner."""
    text = Text()
    text.append("Spotify Concert Finder\n", style="bold green")
    text.append(f"Logged in as: ", style="dim")
    text.append(display_name or username, style="bold cyan")
    console.print(Panel(text, border_style="green", padding=(1, 4)))


def print_artists_table(artists: List[Artist], title: str) -> None:
    """Render a Rich table of artists."""
    if not artists:
        console.print(f"[yellow]No artists found for: {title}[/yellow]")
        return

    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold magenta",
        show_lines=False,
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Artist", style="bold white", min_width=20)
    table.add_column("Genres", style="cyan", min_width=25)
    table.add_column("Popularity", justify="center", width=12)

    for i, artist in enumerate(artists, 1):
        genres = ", ".join(artist.genres[:3]) if artist.genres else "—"
        popularity_bar = _popularity_bar(artist.popularity)
        table.add_row(str(i), artist.name, genres, popularity_bar)

    console.print(table)


def print_concerts_table(concerts: List[Concert], title: str) -> None:
    """Render a Rich table of upcoming concerts."""
    if not concerts:
        console.print(Panel(
            "[yellow]No upcoming concerts found for your artists in the selected region.[/yellow]",
            title=title,
            border_style="yellow",
        ))
        return

    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="bright_green",
        header_style="bold magenta",
        show_lines=True,
    )

    table.add_column("Artist", style="bold white", min_width=18)
    table.add_column("Event", style="cyan", min_width=22)
    table.add_column("Date", style="green", width=12)
    table.add_column("Time", style="dim", width=7)
    table.add_column("Venue", style="white", min_width=20)
    table.add_column("City", style="yellow", min_width=14)
    table.add_column("Country", style="dim", width=10)
    table.add_column("Tickets", style="bright_cyan", min_width=10)

    for concert in concerts:
        ticket_cell = "[link={0}]Buy[/link]".format(concert.ticket_url) if concert.ticket_url else "—"
        table.add_row(
            concert.artist,
            concert.event_name,
            concert.date,
            concert.time or "—",
            concert.venue,
            concert.city,
            concert.country,
            ticket_cell,
        )

    console.print(table)
    console.print(f"[dim]Found {len(concerts)} concert(s)[/dim]")


def print_searching(artist_name: str) -> None:
    """Print a status line while searching."""
    console.print(f"  [dim]Searching concerts for[/dim] [cyan]{artist_name}[/cyan]...", end="\r")


def print_no_credentials_warning() -> None:
    """Warn user about missing Spotify credentials."""
    console.print(Panel(
        "[bold red]Missing Spotify credentials![/bold red]\n\n"
        "Please create a [bold].env[/bold] file in the project root with:\n"
        "  • [cyan]SPOTIFY_CLIENT_ID[/cyan] and [cyan]SPOTIFY_CLIENT_SECRET[/cyan]\n"
        "    → Create an app at [link=https://developer.spotify.com/dashboard]developer.spotify.com/dashboard[/link]\n"
        "    → Set redirect URI to [bold]http://localhost:8888/callback[/bold]\n\n"
        "No Bandsintown key needed — it works out of the box.",
        title="Setup Required",
        border_style="red",
        padding=(1, 2),
    ))


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")


def print_section(title: str) -> None:
    console.print(f"\n[bold bright_blue]{title}[/bold bright_blue]")
    console.print("─" * len(title), style="bright_blue")


# --- Helpers ---

def _popularity_bar(score: int) -> str:
    """Convert 0-100 popularity to a visual bar."""
    filled = round(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar} {score}"
