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

**Supports YouTube, YouTube Music, SoundCloud, Spotify, Deezer, Bandcamp, Apple Music, Tidal, Amazon Music.**  
Type `/play <url or query>` and let the music flow~

<a id="spotify-support"></a>
## (＾◡＾) Spotify Support

* ✅ Individual tracks  
* ✅ Personal & public playlists  
* ✅ Spotify-curated mixes (e.g., *Release Radar*, *Your Mix*) via SpotifyScraper—bypasses API limits!

> *Note:* Dynamic Spotify radios/mixes may vary from your app—they update constantly.

<a id="key-features"></a>
## (≧◡≦) Key Features

* Play from **9+ platforms**: YouTube • SoundCloud • Spotify • Deezer • Bandcamp • Apple Music • Tidal • Amazon Music  
* Slash commands: `/play`, `/pause`, `/skip`, `/queue`, `/clearqueue`, + more!  
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
````

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

| Command             | Description                               |
| ------------------- | ----------------------------------------- |
| `/play <url/query>` | Add a song or playlist                    |
| `/pause`            | Pause playback                            |
| `/resume`           | Resume playback                           |
| `/skip`             | Skip current track                        |
| `/stop`             | Stop and clear queue                      |
| `/queue`            | Show current queue                        |
| `/clearqueue`       | Clear the queue                           |
| `/playnext <...>`   | Queue to play next                        |
| `/nowplaying`       | Display current track info                |
| `/loop`             | Toggle loop on current track              |
| `/shuffle`          | Shuffle the queue                         |
| `/autoplay`         | Toggle autoplay of similar tracks         |
| `/filter <type>`    | Apply audio filters (nightcore, bass+...) |
| `/lyrics`           | Fetch lyrics via Genius                   |
| `/karaoke`          | Sing along with synced lyrics             |
| `/24_7 <on/off>`    | Stay connected indefinitely               |
| `/reconnect`        | Force reconnect if voice issues           |
| `/status`           | Show bot resource usage                   |
| `/kaomoji`          | Toggle kawaii mode                        |
| `/discord`          | Get invite to support server              |

<a id="troubleshooting"></a>

## (｀・ω・´) Troubleshooting

* **FFmpeg not found**: Ensure it's installed & in your PATH
* **Spotify errors**: Verify API credentials in `.env`
* **Bot offline/unresponsive**: Check `DISCORD_TOKEN` and permissions

<a id="privacy--data"></a>

## (ﾉ◕ヮ◕)ﾉ Privacy & Data

* **Self-hosted**: All logs are local, no telemetry.
* **Public bot**: Minimal error logs only, no tracking or analytics.

<a id="contribute--support"></a>

## (ง＾◡＾)ง Contribute & Support

* Fork the repo, open an issue or PR—fixes get merged faster!
* Star the repo if you enjoy it!
* Join our Discord server:
  [![Discord](https://img.shields.io/discord/1395755097350213632?label=Discord%20Server\&logo=discord)](https://discord.gg/JeH8g6g3cG)
* Become a Patron on [Patreon](https://patreon.com/Playify) for a special backer shoutout and gratitude!
* Sponsor via PayPal for faster bugfixes:

  * [Donate via PayPal](https://www.paypal.com/paypalme/alanmussot1)

<a id="license"></a>

## (＾ω＾) License

MIT License — do what you want, just be kind!

<p align="center">
  Built with ☕ and love by <a href="https://github.com/alan7383">alan7383</a> (｡♥‿♥｡)
</p>
