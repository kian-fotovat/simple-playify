<h1 align="center">Playify ♪(｡◕‿◕｡)</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="Playify Banner" width="900">
</p>

---

## ＼( O_O )／ What is Playify?

A super cute, open-source Discord music bot that just wants to play good music for you...  
No ads, no weird premium tiers, just tunes and good vibes~ (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧

---

## (｡♥‿♥｡) Supported Platforms

> YouTube • YouTube Music • SoundCloud • Spotify  
> Deezer • Bandcamp • Apple Music • Tidal • Amazon Music

---

## (o･ω･)ﾉ Manual Setup

### 1. Clone the repo
```bash
git clone https://github.com/alan7383/playify.git
cd playify
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install
```

### 3. Set up your secrets

```bash
cp .env.example .env
# Then edit .env with your tokens!
```

### 4. Run the bot!

```bash
python playify.py
```

> (O\_O;) Make sure **FFmpeg** is installed and added to your PATH!

---

## (´-ω-\`) Environment Variables

Create a `.env` file like this:

```env
DISCORD_TOKEN=your_discord_bot_token_here
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
GENIUS_TOKEN=your_genius_api_token_here
```

> (¬\_¬) Shhh... Don't commit your `.env` file! It’s secret for a reason\~

---

## (ﾉ´ヮ´)ﾉ\*:･ﾟ✧ Features

・ Plays from over 9 platforms! (so friendly\~)
・ Real-time audio filters like slowed, reverb, nightcore\~
・ Karaoke mode with synced lyrics ♪
・ Loop, shuffle, and autoplay so the music never stops\~
・ `/kaomoji` mode for extra cuteness! (◕‿◕✿)
・ Simple slash commands anyone can use\~
・ No data collection at all! (｡•́︿•̀｡)✧

---

## (・◇・) Command List

| Command                 | Description                                 |
| ----------------------- | ------------------------------------------- |
| `/play <url/query>`     | Add a song or playlist ♪(´▽｀)               |
| `/pause`                | Pause the music (´･\_･\`)                   |
| `/resume`               | Resume the music\~ o(≧▽≦)o                  |
| `/skip`                 | Skip to the next track (ノ°ο°)ノ              |
| `/stop`                 | Stop and rest (ﾉ´･ω･)ﾉ ﾐ ┸━┸                |
| `/queue`                | Show the current queue (◕‿◕)ノ               |
| `/clearqueue`           | Clear the queue! (≧▽≦)                      |
| `/playnext <url/query>` | Play something right after this one (っ◕‿◕)っ |
| `/nowplaying`           | What’s this song? ヽ(o^ ^o)ﾉ                 |
| `/loop`                 | Loop the current track ( •̀ ω •́ )✧         |
| `/shuffle`              | Shuffle the queue\~ (✿◕‿◕)                  |
| `/autoplay`             | Autoplay when queue ends (b ᵔ▽ᵔ)b           |
| `/filter`               | Apply audio filters! (⌐■\_■)                |
| `/lyrics`               | Get the lyrics φ(..)                        |
| `/karaoke`              | Sing along with synced lyrics\~             |
| `/24_7 <mode>`          | Stay connected forever (￣^￣)ゞ               |
| `/reconnect`            | Reconnect if it’s buggy (o\_O;)             |
| `/status`               | See resource usage (⌐□\_□)                  |
| `/kaomoji`              | Toggle cute mode! (◕‿◕✿)                    |
| `/discord`              | Join the support server! ヽ(・∀・)ﾉ            |

---

## ( ´ ▽ \` )ﾉ License

MIT License — do what you want, just be kind\~

---

## (・\_・?) Support

Have a question? Got a cool idea?

・ [Join the Discord Server](https://discord.gg/yourserverlink) — come say hi\~
・ [Patreon](https://patreon.com/yourpatreon) — support Playify and get a special role\~
・ [PayPal](https://paypal.me/yourpaypal) — help keep Playify alive and ad-free!

> Your support keeps me going! (๑>ᴗ<๑)

---

<p align="center">
  Built with love and coffee by <a href="https://github.com/alan7383">alan7383</a> (｡♥‿♥｡)
</p>
