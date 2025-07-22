<h1 align="center">Playify ♪(｡◕‿◕｡)</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="Playify Banner" width="900">
</p>

---

<p align="center">
  <img src="https://img.shields.io/github/license/alan7383/playify.svg" alt="GitHub license" />
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+" />
  <a href="https://discord.gg/JeH8g6g3cG"><img src="https://img.shields.io/discord/1395755097350213632?label=Discord%20Server&logo=discord" alt="Discord Server" /></a>
</p>

---

## Table of Contents

* [What is Playify?](#what-is-playify)
* [Spotify Support](#spotify-support)
* [Key Features](#key-features)
* [Installation & Self-Hosting](#installation--self-hosting)
* [Command Reference](#command-reference)
* [Troubleshooting](#troubleshooting)
* [Privacy & Data](#privacy--data)
* [Contribute & Support](#contribute--support)
* [License](#license)

---

<a id="what-is-playify"></a>
## ＼(＾O＾)／ What is Playify?

Playify is the ultimate minimalist Discord music bot—no ads, no premium tiers, no limits, just music and kawaii vibes!

* **No web UI**: Only simple slash commands.
* **100% free**: All features unlocked for everyone.
* **Unlimited playback**: Giant playlists, endless queues, eternal tunes!

**Supports YouTube, YouTube Music, SoundCloud, Spotify, Deezer, Bandcamp, Apple Music, Tidal, Amazon Music, and local files.**
Type `/play <url or query>` and let the music flow~

<a id="spotify-support"></a>
## (＾◡＾) Spotify Support

* ✅ Individual tracks
* ✅ Personal & public playlists
* ✅ Spotify-curated mixes (e.g., *Release Radar*, *Your Mix*) via [SpotifyScraper](https://github.com/AliAkhtari78/SpotifyScraper)—bypasses API limits!

> *Note:* Dynamic Spotify radios/mixes may vary from your app—they update constantly.

<a id="key-features"></a>
## (≧◡≦) Key Features

* Play from **10+ sources**: YouTube • SoundCloud • Spotify • Deezer • Bandcamp • Apple Music • Tidal • Amazon Music • **Local Files**
* Slash commands: `/play`, `/pause`, `/skip`, `/queue`, `/remove`, + more!
* **Play Local Files**: Directly upload and play your own audio/video files.
* **Autoplay** of similar tracks (YouTube Mix, SoundCloud Stations)
* **Loop** & **shuffle** controls
* **Kawaii Mode** toggles cute kaomoji responses (`/kaomoji`)
* Audio **filters**: slowed, reverb, bass boost, nightcore, and more
* Powered by `yt-dlp`, `FFmpeg`, `asyncio`, and a dash of chaos

<a id="installation--self-hosting"></a>
## (＾∀＾) Installation & Self-Hosting

*For a more detailed step-by-step guide, see the [Wiki](https://github.com/alan7383/playify/wiki).*

**Requirements:**

* Python 3.9+
* FFmpeg installed & in PATH
* Git
* Discord Bot Token
* (Optional) Spotify API credentials
* (Optional) Genius API token for lyrics

**Setup Steps:**

1. Clone the repo:

   ```bash
   git clone https://github.com/alan7383/playify.git
   cd playify
    ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. Copy & configure environment:

   ```bash
   cp .env.example .env
   ```

   *Edit `.env`:*

   ```ini
   DISCORD_TOKEN=your_discord_bot_token
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   GENIUS_TOKEN=your_genius_api_token
   ```

4. Run the bot:

   ```bash
   python playify.py
   ```

5. Invite to Discord:

   * Enable **Guilds** & **Voice States** intents in the Developer Portal
   * Generate invite link with: Connect, Speak, Send Messages
   * Add the bot and enjoy `/play`!

<a id="command-reference"></a>

## (⊙‿⊙) Command Reference

| Command | Description |
| :--- | :--- |
| `/play <url/query>` | Add a song or playlist from a link or search. |
| `/play-files <file1...>` | Play one or more uploaded audio/video files. |
| `/playnext <query/file>` | Add a song or local file to the front of the queue. |
| `/pause` | Pause playback. |
| `/resume` | Resume playback. |
| `/skip` | Skip the current track. |
| `/stop` | Stop playback, clear queue, and disconnect. |
| `/nowplaying` | Display the current track's information. |
| `/queue` | Show the current song queue with interactive pages. |
| `/remove` | Open a menu to remove specific songs from the queue. |
| `/shuffle` | Shuffle the queue. |
| `/clearqueue` | Clear all songs from the queue. |
| `/loop` | Toggle looping for the current track. |
| `/autoplay` | Toggle autoplay of similar songs when the queue ends. |
| `/24_7 <mode>` | Keep the bot in the channel (`normal`, `auto`, or `off`). |
| `/filter` | Apply real-time audio filters (nightcore, bassboost...). |
| `/lyrics` | Fetch and display lyrics for the current song. |
| `/karaoke` | Start a karaoke session with synced lyrics. |
| `/reconnect` | Refresh the voice connection to fix lag without losing your place. |
| `/status` | Show the bot's detailed performance and resource usage. |
| `/kaomoji` | Toggle cute kaomoji responses. `(ADMIN)` |
| `/discord` | Get an invite to the official support server. |

<a id="troubleshooting"></a>

## (｀・ω・´) Troubleshooting

* **FFmpeg not found**: Ensure it's installed & in your system's PATH.
* **Spotify errors**: Verify your API credentials in the `.env` file.
* **Bot offline/unresponsive**: Check your `DISCORD_TOKEN` and bot permissions in the Developer Portal.

<a id="privacy--data"></a>

## (ﾉ◕ヮ◕)ﾉ Privacy & Data

* **Self-hosted**: All logs are local to your machine. No telemetry is sent.
* **Public bot**: Minimal error logs are stored for debugging purposes only. No user data or analytics are collected.

<a id="contribute--support"></a>

## (ง＾◡＾)ง Contribute & Support

* Fork the repo, open an issue or pull request—all contributions are welcome!
* Star the repository if you enjoy using Playify!
* Join our Discord server for help and community discussions:
  [![Discord](https://img.shields.io/discord/1395755097350213632?label=Discord%20Server&logo=discord)](https://discord.gg/JeH8g6g3cG)
* Support the project to help cover hosting costs and encourage development:
  * Become a Patron on [Patreon](https://patreon.com/Playify) for special perks and to show your ongoing support!
  * [Donate via PayPal](https://www.paypal.com/paypalme/alanmussot1) for a one-time contribution.

<a id="license"></a>

## (＾ω＾) License

MIT License — do what you want with the code, just be kind!

<p align="center">
  Built with ☕ and love by <a href="https://github.com/alan7383">alan7383</a> (｡♥‿♥｡)
</p>
