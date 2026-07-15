# Spotify Concert Finder

---

_For Doris_  
_my favourite person in every room, in every city, in every crowd._

There is a particular kind of magic that only happens live. When the lights
go low and the first note rings out and the whole world contracts to just
that stage, that song, that moment and suddenly every worry you carried
in with you dissolves into something bigger than yourself. You told me more
times then i could count, that music does that to you. That it reaches
somewhere words cannot. That you can't just listen to it, it isn't enough.
_It has to reach your soul_.

I have spent a long time watching the way your eyes light up when a song
you love comes on. The way you close them sometimes, just for a moment, like
you are trying to hold the feeling still. Or during our car rides, when you
start staring into the distance and nothing could come between you, the music
and the current moment. I would give anything to fill your life with more of
those moments.

So I did what I know how to do. I wrote you something.

It is not flowers or poetry even though you deserve both, always. It is
something I hope will keep giving long after tonight. Open it up, and it
will reach into the music you carry around in your heart every day, and
turn it into nights you will never forget. Concerts in cities near and far,
artists who speak the language only you fully understand, stages waiting
for you to find them.

You once said you wished you could go to more live shows. I heard you.
_I always hear you_, even the things you say quietly, even the things you
only half-say.

This is for every concert you have not yet been to.
Every song not yet heard live.
Every night not yet danced through.

Go find them all, _Srce_.  
I will be right there beside you.

_Yours, always_  
_Liam_

---

## What It Does

Spotify Concert Finder is a terminal application that connects to your Spotify account, reads your top played and followed artists, and searches for upcoming concerts using the Bandsintown API. Filter by country, continent, city, date range — and export the results to Excel with one click.

---

## Features

- **Artist sources** — browse your top played artists (last 4 weeks, 6 months, or all time), your followed artists, or search for any artist manually
- **Mix and match** — combine multiple sources, remove artists you don't want, add more, or start over
- **Concert search** — search by continent, individual countries, or all locations worldwide
- **City + radius** — narrow results to within 25 / 50 / 100 / 200 / 500 km of a specific city
- **Date range** — preset filters (next 1, 3, 6, 12 months) or a custom month/year range
- **Excel export** — save results to `C:\Users\{you}\concerts\concerts_YYYY-MM-DD_HH-MM-SS.xlsx` with clickable ticket links
- **Account switching** — logout and switch to a different Spotify account at any time
- **Developer mode** — password-protected mode that surfaces API errors and debug information
- **Auto-updates** — checks GitHub every 30 days and updates itself automatically

---

## Quick Start (Windows)

1. Double-click `launch.bat`

That's it. The launcher will:

- Install Python automatically if not present (no admin rights required)
- Create a virtual environment
- Install all dependencies
- Launch the app

On first run you will be asked to log in to Spotify in your browser. After that the token is cached and login is automatic.

---

## Manual Setup

If you prefer to set up manually in the terminal:

```cmd
cd path\to\spotifyApp

:: Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Run the app
python main.py
```

---

## Configuration

Create a `.env` file in the project root:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
BANDSINTOWN_APP_ID=your_bandsintown_account_id
DEV_PASSWORD=your_developer_password
```

| Variable                | Required | Default                          | Description                                      |
| ----------------------- | -------- | -------------------------------- | ------------------------------------------------ |
| `SPOTIFY_CLIENT_ID`     | Yes      | —                                | From Spotify Developer Dashboard                 |
| `SPOTIFY_CLIENT_SECRET` | Yes      | —                                | From Spotify Developer Dashboard                 |
| `SPOTIFY_REDIRECT_URI`  | No       | `http://localhost:8888/callback` | Must match what you set in the Spotify dashboard |
| `BANDSINTOWN_APP_ID`    | Yes      | —                                | Your Bandsintown account ID                      |
| `DEV_PASSWORD`          | No       | —                                | Password to unlock Developer mode                |

---

## Spotify Setup

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Fill in a name and description
4. Set the redirect URI to `http://localhost:8888/callback`
5. Copy the **Client ID** and **Client Secret** into your `.env` file

---

## Bandsintown Setup

1. Sign up at [artists.bandsintown.com](https://artists.bandsintown.com)
2. Go to your account settings
3. Copy your **Account ID** (a numeric value) into your `.env` as `BANDSINTOWN_APP_ID`

> **Note:** Only numeric account IDs are accepted by the Bandsintown API.

---

## First Login

On first run, the app opens your browser and asks you to log in to Spotify and approve access. After you approve, you are redirected to `http://localhost:8888/callback` and the app captures the token automatically. The token is cached at `~/.spotifyapp_cache` — on subsequent runs login is instant and silent.

To log in as a different account, select **Logout & switch account** from the main menu.

---

## Developer Mode

Developer mode surfaces API errors and per-artist debug statistics that are hidden in normal mode. It is password-protected.

To enable it:

1. Set `DEV_PASSWORD=your_password` in your `.env` file
2. On startup, select **Developer mode** from the run mode prompt
3. Enter your password (3 attempts allowed)

In developer mode you will see:

- The Bandsintown app_id being used
- Your Spotify user ID
- Per-artist API errors with tips for fixing them
- How many events were fetched and how many passed the country filter

---

## Auto-Updates

The app checks for updates every 30 days automatically on startup. If a newer version is available on GitHub it runs `git pull`, then restarts itself transparently. No action is required from you.

The date of the last check is stored in `~/.spotifyapp_update_check`.

> **Requires:** Git must be installed and the project must be a git repository with `origin` pointing to GitHub.

---

## Excel Export

After a concert search, if results are found, you will be asked:

```
Export results to Excel? (y/N)
Save as: C:\Users\yourname\concerts\concerts_2026-07-15_14-32-07.xlsx
```

The `concerts\` folder is created automatically. The Excel file includes:

- All concert columns: Artist, Event, Date, Time, Venue, City, Country
- Clickable ticket links in the Tickets column
- Bold green header row
- Frozen header row for easy scrolling
- Auto-fitted column widths

---

## Project Structure

```
spotifyApp/
├── main.py                  # Entry point and app flow
├── config.py                # Loads .env and exports settings
├── updater.py               # Auto-update logic (git pull every 30 days)
├── requirements.txt         # Python dependencies
├── launch.bat               # Windows launcher (auto-installs Python + deps)
├── .env                     # Your credentials (not committed to git)
├── .gitignore
│
├── auth/
│   └── spotify_auth.py      # Spotify OAuth2 + token caching + logout
│
├── spotify/
│   ├── models.py            # Artist dataclass
│   └── client.py            # Spotify API — top artists, followed artists, search
│
├── bandsintown/
│   ├── models.py            # Concert dataclass
│   └── client.py            # Bandsintown API — fetch and filter events
│
└── ui/
    ├── display.py           # Rich terminal tables, panels, Excel export
    └── menus.py             # Questionary interactive prompts and menus
```

---

## Dependencies

| Library         | Version  | Purpose                                      |
| --------------- | -------- | -------------------------------------------- |
| `spotipy`       | >=2.23.0 | Spotify Web API client + OAuth2              |
| `requests`      | >=2.31.0 | Bandsintown API HTTP calls                   |
| `rich`          | >=13.7.0 | Terminal tables, panels, and formatting      |
| `questionary`   | >=2.0.1  | Interactive menus, prompts, and autocomplete |
| `python-dotenv` | >=1.0.0  | Load credentials from `.env`                 |
| `openpyxl`      | >=3.1.0  | Excel file export                            |

---

## License

Personal project — not licensed for redistribution.
