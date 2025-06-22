<h1 align="center">Playify ♪( ° □ °) ♪</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="Playify Banner" width="900">
</p>

---

## ＼(ノºДº)ノ What is Playify?

Playify is a minimalist Discord music bot that gets the job done. No fluff, no fuss—just pure music playback with a touch of charm.

- **No web UI.** Just clean, simple commands.
- **No premium tier.** Everything’s free, always.
- **No limits.** Play giant playlists, queue endless tracks, vibe without restrictions.

**Supports YouTube, YouTube Music, SoundCloud, Spotify, Deezer, Bandcamp, Apple Music, Tidal, and Amazon Music.** Type `/play`, and let the music roll.

---

## (＾□＾) Spotify Support

Playify handles Spotify like a pro:

- ✅ **Individual tracks**: Plays them instantly.
- ✅ **Playlists**: From small to massive, it’s all good.
- ⚠️ **Spotify-curated playlists** (e.g., "This Is", "Your Mix", "Release Radar") aren’t supported due to API limitations. Blame Spotify, not us.

---

## (｡‿‿｡) Features

- Play music from **YouTube, YouTube Music, SoundCloud, Spotify, Deezer, Bandcamp, Apple Music, Tidal, and Amazon Music**.
- Intuitive commands: `/play`, `/pause`, `/skip`, `/queue`, and more.
- **Autoplay** for similar tracks (YouTube Mix, SoundCloud Stations).
- **Looping** and **shuffling** for ultimate playlist control.
- **Kawaii mode** for extra cute responses (toggle with `/kaomoji`).
- **Multilingual**: English and French support (set with `/language`).
- Powered by `yt-dlp`, `FFmpeg`, `asyncio`, and a sprinkle of chaos.

---

## (◕‿◕)ノ Self-Hosting Playify

Want to run Playify yourself? It’s straightforward.

### Requirements

- **Python 3.9+**: [Download here](https://www.python.org/downloads/).
- **FFmpeg**: For audio processing. Install it:
  - **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - **Windows**: Download from [FFmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
- **Playwright**: For processing Apple Music, Tidal, and Amazon Music links. Install it:
   ```bash
   playwright install
  ````

* **Git**: To clone the repo.
* **Discord Bot Token**: Get it from the [Discord Developer Portal](https://discord.com/developers/applications).
* **Spotify API Credentials** (optional, for Spotify support): Create an app on the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).

### Setup Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/alan7383/playify.git
   cd playify
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` is missing, install manually:

   ```bash
   pip install discord.py yt-dlp spotipy cachetools python-dotenv playwright
   ```

3. **Run the bot**:

   ```bash
   python playify.py
   ```

4. **Invite the bot** to your server:

   * Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   * Create an application, add a bot, and enable **Guilds** and **Voice States** intents.
   * Generate an invite link with permissions: `Connect`, `Speak`, `Send Messages`.
   * Add the bot to your server and test with `/play`.

---

### Troubleshooting

* **FFmpeg not found**: Ensure FFmpeg is installed and added to your system PATH.
* **Spotify errors**: Verify your Spotify API credentials and ensure your app is set up correctly.
* **Bot not responding**: Check the Discord token and ensure the bot has proper permissions.

---

## (´・ω・\`)ノ Don’t Want to Self-Host?

No problem! Playify is running 24/7. Invite it to your server:

👉 [Add to Discord](https://alan7383.github.io/playify/)

---

## (・Д・)ノ♥ Privacy First

Your music, your business. Whether you host it yourself or use the hosted Playify bot, **no user data is ever collected or stored**.

* If you're self-hosting: logs stay **local**, only used for debugging — no tracking, no analytics, no nonsense.
* If you're using the public Playify bot: only minimal logs (like errors) are kept **temporarily** to help fix bugs. **No playback history, no user tracking, ever.**

If something breaks, I check the logs.
If it works, enjoy the tunes 🎶

![a39773b9-3362-41ba-b23d-475368f1d07e](https://github.com/user-attachments/assets/9ddd2662-b2fc-4781-a174-d1162149a695)

---

## (≧□≦)ノ Contribute

Got ideas? Fork the repo, make a PR, or report issues. If it fixes something annoying, it might get merged faster.

---

## (･∀･)♡ Support the Chaos

Keep Playify ad-free and running smoothly:

👉 [Paypal](https://www.paypal.com/paypalme/alanmussot1)

Your support might make bug fixes *slightly* faster. No promises.

---

## (⊙‿‿⊙) License

MIT License. Do whatever you want with it, just don’t break anything (too badly).

---

<p align="center">Built with 💢 and ☕ by alan7383</p>
