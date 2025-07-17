<h1 align="center">Playify ♪( ° □ °) ♪</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="Playify Banner" width="900">
</p>

---

## ＼(ノºДº)ノ What is Playify?

Playify is a **minimalist**, **open-source** Discord music bot that **just works**.  
No premium tier, no web dashboard, no tracking — just **pure music and vibes**.

✅ Supports:  
YouTube, YouTube Music, SoundCloud, Spotify, Deezer, Bandcamp, Apple Music, Tidal, Amazon Music

---

## 🐳 Docker Quick Start (Recommended)

### ✅ One-liner install
```bash
git clone https://github.com/alan7383/playify.git
cd playify
cp .env.example .env
# Edit .env with your tokens
docker compose up --build
```

---

## 🧰 Manual Setup (without Docker)

### 🔧 Requirements
- Python 3.9+
- FFmpeg
- Discord Bot Token
- (Optional) Spotify API & Genius API

### 📦 Install
```bash
git clone https://github.com/alan7383/playify.git
cd playify
pip install -r requirements.txt
playwright install
cp .env.example .env
# Edit .env with your tokens
python playify.py
```

---

## 📁 Environment Variables

Create a `.env` file in the root folder:

```env
DISCORD_TOKEN=your_discord_bot_token_here
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
GENIUS_TOKEN=your_genius_api_token_here
```

> ⚠️ Never commit `.env` to GitHub. It’s ignored by `.gitignore`.

---

## 🎶 Features

- ✅ Play from 9+ platforms
- ✅ Real-time audio filters (slowed, bass boost, nightcore...)
- ✅ Karaoke mode with synced lyrics
- ✅ Autoplay, shuffle, queue, loop
- ✅ Kawaii mode toggle
- ✅ Slash commands only
- ✅ Zero tracking, zero logs stored

---

## 🧪 Commands

| Command | Description |
|--------|-------------|
| `/play <url or query>` | Play a song or playlist |
| `/queue` | Show current queue |
| `/clearqueue` | Clear the current queue |
| `/playnext <url or query>` | Add a song to play next |
| `/nowplaying` | Show the current song playing |
| `/pause` | Pause the current playback |
| `/resume` | Resume the playback |
| `/skip` | Skip to the next song |
| `/loop` | Enable/disable looping for the current song |
| `/stop` | Stop playback and disconnect the bot |
| `/shuffle` | Shuffle the current queue |
| `/autoplay` | Enable/disable autoplay of similar songs |
| `/filter` | Apply or remove audio filters in real time |
| `/lyrics` | Get song lyrics from Genius |
| `/karaoke` | Start a synced karaoke-style lyrics display |
| `/status` | Displays the bot's full performance and diagnostic stats |
| `/kaomoji` | Enable/disable kawaii mode |

---

## 📄 License

MIT License — do whatever you want, just don’t break it (too badly).

---

## ❤️ Support

If you want to help keep Playify ad-free and running:

👉 [PayPal](https://paypal.me/alanmussot1)

---

<p align="center">Built with 💢 and ☕ by <a href="https://github.com/alan7383">alan7383</a></p>
