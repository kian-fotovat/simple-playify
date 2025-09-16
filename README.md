<h1 align="center">Playify ♪(｡◕‿◕｡)</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="Playify Banner" width="900">
</p>

---

<p align="center">
  <img src="https://img.shields.io/github/license/alan7383/playify.svg" alt="GitHub license" />
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+" />
</p>

---

## Table of Contents

* [Easy Windows Setup](#easy-setup)
* [What is Playify?](#what-is-playify)
* [Spotify Support](#spotify-support)
* [Key Features](#key-features)
* [Installation](#installation)
* [Use the Public Bot](#public-bot)
* [Command Reference](#command-reference)
* [Troubleshooting](#troubleshooting)
* [Privacy & Data](#privacy--data)
* [Contributing & Support](#contributing--support)
* [License](#license)

---


<a id="easy-setup"></a>
## Easy Windows Setup (just once, promise)

Too lazy to mess with Python or configs? 
No worries — I made a Windows app that sets up everything for you in one go!  
You'll just need to enter your **Discord token** + **Spotify API keys** once, and you're done forever!

**Get it here:**  
📄 [Instructions & info](https://alan7383.github.io/playify/self-host.html)  

---

<a id="what-is-playify"></a>
## What is Playify?

Playify is the ultimate minimalist Discord music bot—no ads, no premium tiers, no limits, just music!

* **No web UI**: Only simple slash commands.
* **100% free**: All features unlocked for everyone.
* **Unlimited playback**: Giant playlists, endless queues, eternal tunes!

**Supports YouTube, YouTube Music, SoundCloud, Twitch, Spotify, Deezer, Bandcamp, and direct audio links.**
Type `/play <url or query>` and let the music flow~

<a id="spotify-support"></a>
## Spotify Support

* ✅ Individual tracks
* ✅ Personal & public playlists
* ✅ Spotify-curated mixes (e.g., *Release Radar*, *Your Mix*) via [SpotifyScraper](https://github.com/AliAkhtari78/SpotifyScraper)—bypasses API limits!

> *Note:* Dynamic Spotify radios/mixes may vary from your app—they update constantly.

<a id="key-features"></a>
## Key Features

* Play from **5+ sources**: YouTube • SoundCloud • Twitch • Spotify • Deezer • Bandcamp • **Direct Audio Links**
* Slash commands: `/play`, `/search`, `/pause`, `/skip`, `/queue`, `/remove`, + more!
* **Direct Audio Links**: Stream music directly from any audio URL (MP3, FLAC, WAV, etc.)
* **Autoplay** of similar tracks (YouTube Mix, SoundCloud Stations)
* **Loop** & **shuffle** controls
* Powered by `yt-dlp`, `FFmpeg`, `asyncio`, and a dash of chaos

<a id="installation"></a>
## Installation

You can run Playify in two ways. The executable is recommended for most users.

### Method 1: Prebuilt Executable (Recommended)

This is the easiest way to get the bot running.

1. **Download the executable from the releases page.**
2. **Run the executable and follow the setup instructions.**

### Method 2: Manual Setup

**Requirements:**
*   Python 3.9+
*   FFmpeg installed & in your system's PATH
*   Git

**Steps:**
1.  Clone the repo:
    ```bash
    git clone https://github.com/alan7383/playify.git
    cd playify
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Copy & configure environment:
    ```bash
    cp .env.example .env
    ```
    **Edit the `.env` file** with your tokens.
4.  Run the bot:
    ```bash
    python playify.py
    ```

### Inviting the Bot to Discord (for both methods)
*   Go to your Discord Developer Portal.
*   Enable the **Guilds**, **Voice States**, and **Message Content** intents for your bot.
*   Generate an invite link with the `Connect`, `Speak`, and `Send Messages` permissions.
*   Add the bot to your server and enjoy `/play`!

---


<a id="command-reference"></a>
## Command Reference

| Command | Description |
| :--- | :--- |
| `/play <url/query>` | Add a song or playlist from a link/search. Supports direct audio links! |
| `/search <query>` | Searches for a song and lets you choose from the top results. |
| `/playnext <query/file>` | Add a song or local file to the front of the queue. |
| `/pause` | Pause playback. |
| `/resume` | Resume playback. |
| `/skip` | Skip the current track. Replays the song if loop is enabled. |
| `/stop` | Stop playback, clear queue, and disconnect. |
| `/nowplaying` | Display the current track's information. |
| `/seek` | Opens an interactive menu to seek, fast-forward, or rewind. |
| `/queue` | Show the current song queue with interactive pages. |
| `/remove` | Open a menu to remove specific songs from the queue. |
| `/shuffle` | Shuffle the queue. |
| `/clearqueue` | Clear all songs from the queue. |
| `/loop` | Toggle looping for the current track. |
| `/autoplay` | Toggle autoplay of similar songs when the queue ends. |
| `/24_7 <mode>` | Keep the bot in the channel (`normal`, `auto`, or `off`). |
| `/reconnect` | Refresh the voice connection to fix lag without losing your place. |
| `/status` | Show the bot's detailed performance and resource usage. |

<a id="troubleshooting"></a>
## Troubleshooting

*   **FFmpeg not found**: Ensure it's installed & in your system's PATH.
*   **Spotify errors**: Verify your API credentials in the `.env` file.
*   **Bot offline/unresponsive**: Check your `DISCORD_TOKEN` and bot permissions in the Developer Portal.
*   **Direct link issues**: Ensure the URL points directly to an audio file and is publicly accessible.

<a id="privacy--data"></a>
## Privacy & Data

*   **Self-hosted**: All logs are local to your machine. No telemetry is sent.

<a id="contributing--support"></a>
## Contributing & Support

*   Fork the repo, open an issue or pull request—all contributions are welcome!
*   Star the repository if you enjoy using Playify!

<a id="license"></a>
## License

MIT License — do what you want with the code, <del>just be kind!</del> feel free to roast my contributions/changes but don't hate on the OG developer(s) please!

<p align="center">
  Built with ☕ and love by <a href="https://github.com/alan7383">alan7383</a>
</p>
