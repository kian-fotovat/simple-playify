<h1 align="center">Playify ♪( ° □ °) ♪</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="Playify Banner" width="900">
</p>

---

## ＼(ノºДº)ノ What is Playify?

A **minimalist**, **open-source** Discord music bot that **just works** — no ads, no tracking, no premium tier.  
Just pure music and good vibes (◕‿◕)ノ

✅ Supports:  
YouTube, YouTube Music, SoundCloud, Spotify, Deezer, Bandcamp, Apple Music, Tidal, Amazon Music

---

## 🧰 Manual Setup (Recommended)

### 1. Clone the repo
```bash
git clone https://github.com/alan7383/playify.git
cd playify
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
playwright install
```

### 3. Set up your `.env`
```bash
cp .env.example .env
# Edit .env with your tokens
```

### 4. Run the bot
```bash
python playify.py
```

> 💡 Make sure **FFmpeg** is installed and in your PATH.

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

## 🎶 Features (◕‿◕)ノ

- 🎵 Play from **9+ platforms**  
- 🎧 Real-time audio filters (slowed, nightcore, bass boost...)  
- 🎤 Karaoke mode with **synced lyrics**  
- 🔁 Loop, shuffle, autoplay  
- 💖 Kawaii mode toggle (`/kaomoji`)  
- 🧪 Slash commands only  
- 🔒 Zero tracking, zero logs stored

---

## 🧪 Command List (with kaomoji style)

| Command | Description |
|---------|-------------|
| `/play <url or query>` | Add a song or playlist to the queue ♪(´▽｀) |
| `/queue` | Show current queue (◕‿◕)ノ |
| `/clearqueue` | Empty the queue (≧▽≦) |
| `/playnext <url>` | Add as next song (っ◕‿◕)っ |
| `/nowplaying` | Show what's playing now ♫♬ |
| `/pause` | Pause music (´･_･`) |
| `/resume` | Resume music ☆*:.｡.o(≧▽≦)o.｡.:*☆ |
| `/skip` | Skip to next track (ノ°ο°)ノ |
| `/loop` | Toggle loop mode 🔁 |
| `/stop` | Stop & disconnect (ﾉ´･ω･)ﾉ ﾐ ┸━┸ |
| `/shuffle` | Shuffle queue (✿◕‿◕) |
| `/autoplay` | Toggle autoplay ♫ |
| `/filter` | Change audio filters 🎧 |
| `/lyrics` | Show lyrics 📜 |
| `/karaoke` | Start synced karaoke 🎤 |
| `/status` | Bot dashboard & stats 📊 |
| `/kaomoji` | Toggle kawaii mode (◕‿◕✿) |

---

## 📄 License

MIT License — do whatever you want, just don’t break it (too badly) (⊙‿‿⊙)

---

## ❤️ Support

Keep Playify ad-free and running:

👉 [PayPal](https://paypal.me/alanmussot1)  
Your support might fix bugs *slightly* faster... no promises (´• ω •`)

---

<p align="center">Built with 💢 and ☕ by <a href="https://github.com/alan7383">alan7383</a></p>
