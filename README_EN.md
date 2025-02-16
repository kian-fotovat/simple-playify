[🇫🇷 Version française](https://github.com/alan7383/playify/blob/main/README.md)

<h1 align="center">

Playify 🎵

---

<img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="image" width="900">

## Features

- Stream music from YouTube and SoundCloud
- Intuitive commands (play, pause, skip, stop, replay, etc.)
- Playlist management: create, organize, and play your favorite playlists
- Ultra-low latency for a seamless listening experience thanks to an optimized architecture (featuring *asyncio*, *yt-dlp*, and *FFmpeg* magic ✨)
- High-quality audio for the best sound experience

---

## Host Playify Yourself

Want to run Playify on your own machine? Here’s how:

### Requirements

1. **Python 3.9 or later** must be installed. You can get it here: [python.org](https://www.python.org/downloads/).
2. **FFmpeg** must be installed and added to your system PATH. Follow this [guide](https://ffmpeg.org/download.html) for installation.
3. A Discord bot token (available from the [Discord Developer Portal](https://discord.com/developers/applications)).
4. Install the required dependencies using `requirements.txt`.

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/alan7383/playify.git
   cd playify
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file to store your Discord token **(optional but recommended)**:
   ```env
   DISCORD_TOKEN=Your_Discord_Token
   ```
   *Never share your Discord token publicly!*

4. **Extra option**: If you don’t like using the terminal, just double-click `lancer_bot.bat` to launch the bot instantly.

5. Start the bot:
   ```bash
   python main.py
   ```
   *If you're on a Unix-based system (Linux/Mac), use `python3 main.py`.*

### Additional Notes

- Make sure the bot has the necessary permissions to join voice channels and send messages.
- If you run into issues, check the logs in the console for more details.

---

## Don't Want to Host Playify Yourself?

No problem! You can invite Playify directly to your servers. It's hosted 24/7 by me. (@alananasssss on Discord)

Click here to add it: [Invite Link](https://discord.com/oauth2/authorize?client_id=1330613913569726575&permissions=8&integration_type=0&scope=bot)

---

## Contribute

Contributions are always welcome! If you want to add new features or fix bugs:

1. Fork this repository
2. Create a new branch for your changes
3. Submit a pull request

### Reporting Issues

If you encounter any issues or have feature suggestions, check the existing issues first or open a new one.

### Support the Project

If you like Playify and want to support its development, you can donate via PayPal: [Support on PayPal](https://www.paypal.com/paypalme/alanmussot1)

---

## License

This project is licensed under the MIT License. Feel free to use, modify, and distribute it. See the [LICENSE](LICENSE) file for more details.
```
