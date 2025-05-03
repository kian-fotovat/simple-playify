[🇫🇷 Version française](https://github.com/alan7383/playify/blob/main/README.md)

<h1 align="center">

Playify 🎵

---

<img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="image" width="900">

## Features

> **📢 Big news!** After **over two months of work**, **Spotify is now supported** in Playify! 🎉  
> 👉 **Currently in beta**: individual Spotify tracks work flawlessly, and **short playlists are supported**.  
> Full playlist support is coming very soon!  

🧡 If you appreciate the effort behind this update, consider supporting the project: [Donate](https://www.paypal.com/paypalme/alanmussot1)

- Stream music from **YouTube**, **SoundCloud**, and **Spotify**
- Simple, intuitive commands (play, pause, skip, stop, replay, etc.)
- Create and manage personal playlists
- Ultra-low latency and seamless playback with an optimized asynchronous architecture (powered by *yt-dlp*, *FFmpeg*, and *asyncio*)
- High-quality audio for the best sound experience

---

## Host Playify Yourself

Want to run Playify on your own machine? Here’s how:

### Requirements

1. **Python 3.9 or later** ➝ [Download Python](https://www.python.org/downloads/)
2. **FFmpeg** ➝ [Installation guide](https://ffmpeg.org/download.html)
3. A **Discord bot token** ➝ [Discord Developer Portal](https://discord.com/developers/applications)
4. A **Spotify Developer account** ➝ [Create an app here](https://developer.spotify.com/dashboard/applications)
5. Install dependencies via `requirements.txt`

### Spotify Configuration

To enable Spotify support:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Create a new application
3. Retrieve your credentials:
   - `Client ID`
   - `Client Secret`
4. In `main.py`, insert your credentials like this:

```python
# Spotify Configuration
SPOTIFY_CLIENT_ID = 'your_client_id'
SPOTIFY_CLIENT_SECRET = 'your_client_secret'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))
````

⚠️ *Never share these credentials publicly!*

---

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/alan7383/playify.git
   cd playify
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file to store your Discord token:

   ```env
   DISCORD_TOKEN=Your_Discord_Token
   ```

4. Optional: Double-click `lancer_bot.bat` to launch the bot without using the terminal.

5. Start the bot:

   ```bash
   python main.py
   ```

   *On Linux/macOS: `python3 main.py`*

---

## Don't Want to Host Playify Yourself?

No worries! Playify is already hosted 24/7 and ready to use.

👉 [Click here to invite it to your server](https://discord.com/oauth2/authorize?client_id=1330613913569726575&permissions=8&integration_type=0&scope=bot)

---

## Contribute

Pull requests and suggestions are always welcome!

1. Fork the repository
2. Create a new branch
3. Submit a pull request

### Found a Bug or Have an Idea?

Check existing [issues](https://github.com/alan7383/playify/issues), or open a new one to let us know!

---

## Support the Project

Enjoying Playify? Especially now with Spotify support? 🎧
Help me keep it running with a small donation:
👉 [Support on PayPal](https://www.paypal.com/paypalme/alanmussot1)

---

## License

This project is licensed under the **MIT License**.
Feel free to use, modify, and share it.
