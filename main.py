import discord
from discord.ext import commands
from discord import app_commands, Embed
import asyncio
import yt_dlp
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
from urllib.parse import urlparse, parse_qs

# Intents pour le bot
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

# Crée le bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration Spotify
SPOTIFY_CLIENT_ID = 'CLIENTIDHERE'
SPOTIFY_CLIENT_SECRET = 'CLIENTSECRETHERE'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Fonction asynchrone pour extraire les informations avec yt_dlp
async def extract_info_async(ydl_opts, query, loop=None):
    if loop is None:
        loop = asyncio.get_running_loop()
    
    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)
    
    return await loop.run_in_executor(None, extract)

# Stockage des informations de lecture, modes et langues par serveur
class MusicPlayer:
    def __init__(self):
        self.voice_client = None
        self.current_task = None
        self.queue = asyncio.Queue()
        self.current_url = None
        self.current_info = None  # Ajouté pour stocker les infos de la chanson actuelle
        self.text_channel = None
        self.loop_current = False
        self.autoplay_enabled = False
        self.last_was_single = False  # Drapeau pour suivre si la dernière piste était unique

# Dictionnaires pour stocker les états par serveur
music_players = {}      # {guild_id: MusicPlayer()}
kawaii_mode = {}       # {guild_id: bool}
server_languages = {}  # {guild_id: "en" or "fr"}

# Fonction pour obtenir le player d'un serveur
def get_player(guild_id):
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer()
    return music_players[guild_id]

# Fonction pour obtenir le mode kawaii d'un serveur
def get_mode(guild_id):
    return kawaii_mode.get(guild_id, False)

# Fonction pour obtenir la langue d'un serveur
def get_language(guild_id):
    return server_languages.get(guild_id, "en")

# Fonction pour obtenir les messages selon la langue et le mode kawaii
def get_messages(message_key, guild_id):
    is_kawaii = get_mode(guild_id)
    lang = get_language(guild_id)
    
    messages = {
        "en": {
            "no_voice_channel": {
                "normal": "You must be in a voice channel to use this command.",
                "kawaii": "(>ω<) You must be in a voice channel!"
            },
            "connection_error": {
                "normal": "Error connecting to the voice channel.",
                "kawaii": "(╥﹏╥) I couldn't connect..."
            },
            "spotify_error": {
                "normal": "Error processing the Spotify link.",
                "kawaii": "(´；ω；`) Oh no! Problem with the Spotify link..."
            },
            "spotify_playlist_added": {
                "normal": "🎶 Spotify Playlist Added",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ SPOTIFY PLAYLIST"
            },
            "spotify_playlist_description": {
                "normal": "**{count} tracks** being added...",
                "kawaii": "**{count} songs** added!"
            },
            "song_added": {
                "normal": "🎵 Added to Queue",
                "kawaii": "(っ◕‿◕)っ ♫ SONG ADDED ♫"
            },
            "playlist_added": {
                "normal": "🎶 Playlist Added",
                "kawaii": "✧･ﾟ: *✧･ﾟ:* PLAYLIST *:･ﾟ✧*:･ﾟ✧"
            },
            "playlist_description": {
                "normal": "**{count} tracks** added to the queue.",
                "kawaii": "**{count} songs** added!"
            },
            "ytmusic_playlist_added": {
                "normal": "🎶 YouTube Music Playlist Added",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ YOUTUBE MUSIC PLAYLIST"
            },
            "ytmusic_playlist_description": {
                "normal": "**{count} tracks** being added...",
                "kawaii": "**{count} songs** added!"
            },
            "video_error": {
                "normal": "Error adding the video or playlist.",
                "kawaii": "(´；ω；`) Something went wrong with this video..."
            },
            "search_error": {
                "normal": "Error during search. Try another title.",
                "kawaii": "(︶︹︺) Couldn't find this song..."
            },
            "now_playing_title": {
                "normal": "🎵 Now Playing",
                "kawaii": "♫♬ NOW PLAYING ♬♫"
            },
            "now_playing_description": {
                "normal": "[{title}]({url})",
                "kawaii": "♪(´▽｀) [{title}]({url})"
            },
            "pause": {
                "normal": "⏸️ Playback paused.",
                "kawaii": "(´･_･`) Music paused..."
            },
            "no_playback": {
                "normal": "No playback in progress.",
                "kawaii": "(・_・;) Nothing is playing right now..."
            },
            "resume": {
                "normal": "▶️ Playback resumed.",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ Let's go again!"
            },
            "no_paused": {
                "normal": "No playback is paused.",
                "kawaii": "(´･ω･`) No music is paused..."
            },
            "skip": {
                "normal": "⏭️ Current song skipped.",
                "kawaii": "(ノ°ο°)ノ Skipped! Next song ~"
            },
            "no_song": {
                "normal": "No song is playing.",
                "kawaii": "(；一_一) Nothing to skip..."
            },
            "loop": {
                "normal": "🔁 Looping for the current song {state}.",
                "kawaii": "🔁 Looping for the current song {state}."
            },
            "loop_state_enabled": {
                "normal": "enabled",
                "kawaii": "enabled (◕‿◕✿)"
            },
            "loop_state_disabled": {
                "normal": "disabled",
                "kawaii": "disabled (︶︹︺)"
            },
            "stop": {
                "normal": "⏹️ Playback stopped and bot disconnected.",
                "kawaii": "(ﾉ´･ω･)ﾉ ﾐ ┸━┸ All stopped! Bye bye ~"
            },
            "not_connected": {
                "normal": "The bot is not connected to a voice channel.",
                "kawaii": "(￣ω￣;) I'm not connected..."
            },
            "kawaii_toggle": {
                "normal": "Kawaii mode {state} for this server!",
                "kawaii": "Kawaii mode {state} for this server!"
            },
            "kawaii_state_enabled": {
                "normal": "enabled",
                "kawaii": "enabled (◕‿◕✿)"
            },
            "kawaii_state_disabled": {
                "normal": "disabled",
                "kawaii": "disabled"
            },
            "language_toggle": {
                "normal": "Language set to {lang} for this server!",
                "kawaii": "Language set to {lang} for this server! (✿◕‿◕)"
            },
            "shuffle_success": {
                "normal": "🔀 Queue shuffled successfully!",
                "kawaii": "(✿◕‿◕) Queue shuffled! Yay! ~"
            },
            "queue_empty": {
                "normal": "The queue is empty.",
                "kawaii": "(´･ω･`) No songs in the queue..."
            },
            "autoplay_toggle": {
                "normal": "Autoplay {state}.",
                "kawaii": "♫ Autoplay {state} (◕‿◕✿)"
            },
            "autoplay_state_enabled": {
                "normal": "enabled",
                "kawaii": "enabled"
            },
            "autoplay_state_disabled": {
                "normal": "disabled",
                "kawaii": "disabled"
            },
            "autoplay_added": {
                "normal": "🎵 Adding similar songs to the queue... (This may take up to 1 minute depending on server load)",
                "kawaii": "♪(´▽｀) Adding similar songs to the queue! ~ (It might take a little while, up to 1 minute!)"
            },
            "queue_title": {
                "normal": "🎶 Queue",
                "kawaii": "🎶 Queue (◕‿◕✿)"
            },
            "queue_description": {
                "normal": "There are **{count} songs** in the queue.",
                "kawaii": "**{count} songs** in the queue! ~"
            },
            "queue_next": {
                "normal": "Next songs:",
                "kawaii": "Next songs: ♫"
            },
            "queue_song": {
                "normal": "- [{title}]({url})",
                "kawaii": "- ♪ [{title}]({url})"
            },
            "clear_queue_success": {
                "normal": "✅ Queue cleared.",
                "kawaii": "(≧▽≦) Queue cleared! ~"
            },
            "play_next_added": {
                "normal": "🎵 Added as next song",
                "kawaii": "(っ◕‿◕)っ ♫ Added as next song ♫"
            },
            "no_song_playing": {
                "normal": "No song is currently playing.",
                "kawaii": "(´･ω･`) No music is playing right now..."
            },
        },
        "fr": {
            "no_voice_channel": {
                "normal": "Tu dois être dans un salon vocal pour utiliser cette commande.",
                "kawaii": "(｡•́︿•̀｡) Tu dois être dans un salon vocal !"
            },
            "connection_error": {
                "normal": "Erreur lors de la connexion au salon vocal.",
                "kawaii": "(╥﹏╥) Je n'ai pas pu me connecter..."
            },
            "spotify_error": {
                "normal": "Erreur lors du traitement du lien Spotify.",
                "kawaii": "(´；ω；`) Oh non ! Problème avec le lien Spotify..."
            },
            "spotify_playlist_added": {
                "normal": "🎶 Playlist Spotify ajoutée",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ PLAYLIST SPOTIFY"
            },
            "spotify_playlist_description": {
                "normal": "**{count} titres** en cours d'ajout...",
                "kawaii": "**{count} musiques** ajoutées !"
            },
            "song_added": {
                "normal": "🎵 Ajouté à la file d'attente",
                "kawaii": "(っ◕‿◕)っ ♫ MUSIQUE AJOUTÉE ♫"
            },
            "playlist_added": {
                "normal": "🎶 Playlist ajoutée",
                "kawaii": "✧･ﾟ: *✧･ﾟ:* PLAYLIST *:･ﾟ✧*:･ﾟ✧"
            },
            "playlist_description": {
                "normal": "**{count} titres** ont été ajoutés à la file d'attente.",
                "kawaii": "**{count} musiques** ajoutées !"
            },
            "ytmusic_playlist_added": {
                "normal": "🎶 Playlist YouTube Music ajoutée",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ PLAYLIST YOUTUBE MUSIC"
            },
            "ytmusic_playlist_description": {
                "normal": "**{count} titres** en cours d'ajout...",
                "kawaii": "**{count} musiques** ajoutées !"
            },
            "video_error": {
                "normal": "Erreur lors de l'ajout de la vidéo ou de la playlist.",
                "kawaii": "(´；ω；`) Problème avec cette vidéo..."
            },
            "search_error": {
                "normal": "Erreur lors de la recherche. Réessaie avec un autre titre.",
                "kawaii": "(︶︹︺) Je n'ai pas trouvé cette musique..."
            },
            "now_playing_title": {
                "normal": "🎵 En cours de lecture",
                "kawaii": "♫♬ MAINTENANT EN LECTURE ♬♫"
            },
            "now_playing_description": {
                "normal": "[{title}]({url})",
                "kawaii": "♪(´▽｀) [{title}]({url})"
            },
            "pause": {
                "normal": "⏸️ Lecture mise en pause.",
                "kawaii": "(´･_･`) Musique en pause..."
            },
            "no_playback": {
                "normal": "Aucune lecture en cours.",
                "kawaii": "(・_・;) Rien ne joue actuellement..."
            },
            "resume": {
                "normal": "▶️ Lecture reprise.",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ C'est reparti !"
            },
            "no_paused": {
                "normal": "Aucune lecture mise en pause.",
                "kawaii": "(´･ω･`) Aucune musique en pause..."
            },
            "skip": {
                "normal": "⏭️ Chanson actuelle ignorée.",
                "kawaii": "(ノ°ο°)ノ Skippé ! Prochaine musique ~"
            },
            "no_song": {
                "normal": "Aucune chanson en cours.",
                "kawaii": "(；一_一) Rien à skipper..."
            },
            "loop": {
                "normal": "🔁 Lecture en boucle pour la musique actuelle {state}.",
                "kawaii": "🔁 Lecture en boucle pour la musique actuelle {state}."
            },
            "loop_state_enabled": {
                "normal": "activée",
                "kawaii": "activée (◕‿◕✿)"
            },
            "loop_state_disabled": {
                "normal": "désactivée",
                "kawaii": "désactivée (︶︹︺)"
            },
            "stop": {
                "normal": "⏹️ Lecture arrêtée et bot déconnecté.",
                "kawaii": "(ﾉ´･ω･)ﾉ ﾐ ┸━┸ J'ai tout arrêté ! Bye bye ~"
            },
            "not_connected": {
                "normal": "Le bot n'est pas connecté à un salon vocal.",
                "kawaii": "(￣ω￣;) Je ne suis pas connecté..."
            },
            "kawaii_toggle": {
                "normal": "Mode kawaii {state} pour ce serveur !",
                "kawaii": "Mode kawaii {state} pour ce serveur !"
            },
            "kawaii_state_enabled": {
                "normal": "activé",
                "kawaii": "activé (◕‿◕✿)"
            },
            "kawaii_state_disabled": {
                "normal": "désactivé",
                "kawaii": "désactivé"
            },
            "language_toggle": {
                "normal": "Langue définie sur {lang} pour ce serveur !",
                "kawaii": "Langue définie sur {lang} pour ce serveur ! (✿◕‿◕)"
            },
            "shuffle_success": {
                "normal": "🔀 File d'attente mélangée avec succès !",
                "kawaii": "(✿◕‿◕) File d'attente mélangée ! Youpi ! ~"
            },
            "queue_empty": {
                "normal": "La file d'attente est vide.",
                "kawaii": "(´･ω･`) Pas de musiques dans la file..."
            },
            "autoplay_toggle": {
                "normal": "Autoplay {state}.",
                "kawaii": "♫ Autoplay {state} (◕‿◕✿)"
            },
            "autoplay_state_enabled": {
                "normal": "activé",
                "kawaii": "activé"
            },
            "autoplay_state_disabled": {
                "normal": "désactivé",
                "kawaii": "désactivé"
            },
            "autoplay_added": {
                "normal": "🎵 Ajout de chansons similaires à la file... (Cela peut prendre jusqu'à 1 minute selon la charge du serveur)",
                "kawaii": "♪(´▽｀) Ajout de chansons similaires à la file ! ~ (Ça peut prendre un petit moment, jusqu'à 1 minute !)"
            },
            "queue_title": {
                "normal": "🎶 File d'attente",
                "kawaii": "🎶 File d'attente (◕‿◕✿)"
            },
            "queue_description": {
                "normal": "Il y a **{count} chansons** dans la file d'attente.",
                "kawaii": "**{count} chansons** dans la file d'attente ! ~"
            },
            "queue_next": {
                "normal": "Chansons suivantes :",
                "kawaii": "Chansons suivantes : ♫"
            },
            "queue_song": {
                "normal": "- [{title}]({url})",
                "kawaii": "- ♪ [{title}]({url})"
            },
            "clear_queue_success": {
                "normal": "✅ File d'attente effacée.",
                "kawaii": "(≧▽≦) File d'attente effacée ! ~"
            },
            "play_next_added": {
                "normal": "🎵 Ajoutée comme prochaine chanson",
                "kawaii": "(っ◕‿◕)っ ♫ Ajoutée comme prochaine chanson ♫"
            },
            "no_song_playing": {
                "normal": "Aucune chanson n'est actuellement en lecture.",
                "kawaii": "(´･ω･`) Aucune musique n'est en lecture actuellement..."
            },
        }
    }
    
    mode = "kawaii" if is_kawaii else "normal"
    return messages[lang][message_key][mode]

# Fonctions utilitaires pour YouTube Mix et SoundCloud Stations
def get_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname in ('www.youtube.com', 'youtube.com', 'youtu.be'):
        if parsed.hostname == 'youtu.be':
            return parsed.path[1:]
        if parsed.path == '/watch':
            query = parse_qs(parsed.query)
            return query.get('v', [None])[0]
    return None

def get_mix_playlist_url(video_url):
    video_id = get_video_id(video_url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"
    return None

def get_soundcloud_track_id(url):
    if "soundcloud.com" in url:
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get("id")
        except Exception:
            return None
    return None

def get_soundcloud_station_url(track_id):
    if track_id:
        return f"https://soundcloud.com/discover/sets/track-stations:{track_id}"
    return None

# Fonction pour traiter les liens Spotify
async def process_spotify_url(url, interaction):
    try:
        if 'track' in url:
            track = sp.track(url)
            query = f"{track['name']} {track['artists'][0]['name']}"
            return [query]
        elif 'playlist' in url:
            results = sp.playlist_tracks(url)
            tracks = results['items']
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
            return [f"{item['track']['name']} {item['track']['artists'][0]['name']}" for item in tracks]
        elif 'album' in url:
            results = sp.album_tracks(url)
            return [f"{item['name']} {item['artists'][0]['name']}" for item in results['items']]
        elif 'artist' in url:
            results = sp.artist_top_tracks(url)
            return [f"{track['name']} {track['artists'][0]['name']}" for track in results['tracks']]
    except Exception as e:
        print(f"Spotify error: {e}")
        embed = Embed(
            description=get_messages("spotify_error", interaction.guild_id),
            color=0xFFB6C1 if get_mode(interaction.guild_id) else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return None

# Commande pour basculer entre les modes kawaii
@bot.tree.command(name="kaomoji", description="Enable/disable kawaii mode")
@app_commands.default_permissions(administrator=True)
async def toggle_kawaii(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    kawaii_mode[guild_id] = not get_mode(guild_id)
    state = get_messages("kawaii_state_enabled", guild_id) if kawaii_mode[guild_id] else get_messages("kawaii_state_disabled", guild_id)
    
    embed = Embed(
        description=get_messages("kawaii_toggle", guild_id).format(state=state),
        color=0xFFB6C1 if kawaii_mode[guild_id] else discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande pour changer la langue
@bot.tree.command(name="language", description="Set the bot's language for this server")
@app_commands.default_permissions(administrator=True)
@app_commands.choices(language=[
    app_commands.Choice(name="English", value="en"),
    app_commands.Choice(name="Français", value="fr")
])
async def set_language(interaction: discord.Interaction, language: str):
    guild_id = interaction.guild_id
    server_languages[guild_id] = language
    lang_name = "English" if language == "en" else "Français"
    
    embed = Embed(
        description=get_messages("language_toggle", guild_id).format(lang=lang_name),
        color=0xFFB6C1 if get_mode(guild_id) else discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /play
@bot.tree.command(name="play", description="Play a link or search for a song")
@app_commands.describe(query="Link or title of the video/song to play")
async def play(interaction: discord.Interaction, query: str):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        embed = Embed(
            description=get_messages("no_voice_channel", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not music_player.voice_client or not music_player.voice_client.is_connected():
        try:
            music_player.voice_client = await interaction.user.voice.channel.connect()
        except Exception as e:
            embed = Embed(
                description=get_messages("connection_error", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"Error: {e}")
            return

    music_player.text_channel = interaction.channel
    await interaction.response.defer()

    spotify_regex = re.compile(r'^(https?://)?(open\.spotify\.com)/.+$')
    soundcloud_regex = re.compile(r'^(https?://)?(www\.)?(soundcloud\.com)/.+$')
    youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
    ytmusic_regex = re.compile(r'^(https?://)?(music\.youtube\.com)/.+$')
    bandcamp_regex = re.compile(r'^(https?://)?([^\.]+)\.bandcamp\.com/.+$')  # Ajout de Bandcamp
    
    is_spotify = spotify_regex.match(query)
    is_soundcloud = soundcloud_regex.match(query)
    is_youtube = youtube_regex.match(query)
    is_ytmusic = ytmusic_regex.match(query)
    is_bandcamp = bandcamp_regex.match(query)  # Détection de Bandcamp
    
    if is_spotify:
        spotify_queries = await process_spotify_url(query, interaction)
        if not spotify_queries:
            return

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "default_search": "ytsearch1",
        }
        
        if len(spotify_queries) == 1:
            # Piste unique
            query = spotify_queries[0]
            try:
                info = await extract_info_async(ydl_opts, query)
                video = info["entries"][0] if "entries" in info else info
                video_url = video["webpage_url"]
                await music_player.queue.put({'url': video_url, 'is_single': True})
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{video['title']}]({video['webpage_url']})",
                    color=0xC7CEEA if is_kawaii else discord.Color.blue()
                )
                embed.set_thumbnail(url=video["thumbnail"])
                if is_kawaii:
                    embed.set_footer(text="☆⌒(≧▽° )")
                await interaction.followup.send(embed=embed)
            except Exception as e:
                print(f"Spotify conversion error: {e}")
                embed = Embed(
                    description=get_messages("search_error", guild_id),
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Playlist
            for spotify_query in spotify_queries:
                try:
                    info = await extract_info_async(ydl_opts, spotify_query)
                    video = info["entries"][0] if "entries" in info else info
                    video_url = video["webpage_url"]
                    await music_player.queue.put({'url': video_url, 'is_single': False})
                except Exception as e:
                    print(f"Spotify conversion error: {e}")
                    continue
            embed = Embed(
                title=get_messages("spotify_playlist_added", guild_id),
                description=get_messages("spotify_playlist_description", guild_id).format(count=len(spotify_queries)),
                color=0xB5EAD7 if is_kawaii else discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            
    elif is_soundcloud or is_youtube or is_ytmusic or is_bandcamp:  # Bandcamp ajouté ici
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": "in_playlist",
                "noplaylist": False,
            }
            info = await extract_info_async(ydl_opts, query)
            
            if "entries" in info:
                # Playlist
                for entry in info["entries"]:
                    if entry:
                        await music_player.queue.put({'url': entry['url'], 'is_single': False})
                if info["entries"] and info["entries"][0]:
                    thumbnail = info["entries"][0].get("thumbnail")
                    embed_title = get_messages("ytmusic_playlist_added", guild_id) if is_ytmusic else get_messages("playlist_added", guild_id)
                    embed_description = get_messages("ytmusic_playlist_description", guild_id).format(count=len(info["entries"])) if is_ytmusic else get_messages("playlist_description", guild_id).format(count=len(info["entries"]))
                    embed = Embed(
                        title=embed_title,
                        description=embed_description,
                        color=0xE2F0CB if is_kawaii else discord.Color.green()
                    )
                    if thumbnail:
                        embed.set_thumbnail(url=thumbnail)
                    await interaction.followup.send(embed=embed)
            else:
                # Piste unique
                await music_player.queue.put({'url': info["webpage_url"], 'is_single': True})
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{info['title']}]({info['webpage_url']})",
                    color=0xFFDAC1 if is_kawaii else discord.Color.blue()
                )
                if info.get("thumbnail"):
                    embed.set_thumbnail(url=info["thumbnail"])
                await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = Embed(
                description=get_messages("video_error", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"Error: {e}")
    else:
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "default_search": "ytsearch1",
            }
            info = await extract_info_async(ydl_opts, query)
            video = info["entries"][0] if "entries" in info else info
            await music_player.queue.put({'url': video["webpage_url"], 'is_single': True})
            
            embed = Embed(
                title=get_messages("song_added", guild_id),
                description=f"[{video['title']}]({video['webpage_url']})",
                color=0xB5EAD7 if is_kawaii else discord.Color.blue()
            )
            if video.get("thumbnail"):
                embed.set_thumbnail(url=video["thumbnail"])
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = Embed(
                description=get_messages("search_error", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"Error: {e}")

    if not music_player.current_task or music_player.current_task.done():
        music_player.current_task = asyncio.create_task(play_audio(guild_id))

@bot.tree.command(name="queue", description="Show the current queue")
async def queue(interaction: discord.Interaction):
    # Déférer la réponse pour éviter le timeout
    await interaction.response.defer()

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    # Si la file d'attente est vide
    if music_player.queue.qsize() == 0:
        embed = Embed(
            description=get_messages("queue_empty", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    # Récupérer les 5 premières chansons (ou ajuster selon tes besoins)
    queue_items = list(music_player.queue._queue)[:5]
    next_songs = []
    for item in queue_items:
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
            }
            info = await extract_info_async(ydl_opts, item['url'])
            title = info.get("title", "Unknown Title")
            url = info.get("webpage_url", item['url'])
            next_songs.append(get_messages("queue_song", guild_id).format(title=title, url=url))
        except Exception as e:
            print(f"Erreur lors de l'extraction des infos : {e}")
            next_songs.append("- Chanson inconnue")
    
    # Créer l'embed avec les infos
    embed = Embed(
        title=get_messages("queue_title", guild_id),
        description=get_messages("queue_description", guild_id).format(count=music_player.queue.qsize()),
        color=0xB5EAD7 if is_kawaii else discord.Color.blue()
    )
    if next_songs:
        embed.add_field(
            name=get_messages("queue_next", guild_id),
            value="\n".join(next_songs),
            inline=False
        )
    
    # Envoyer la réponse finale
    await interaction.followup.send(embed=embed)

# Commande /clearqueue
@bot.tree.command(name="clearqueue", description="Clear the current queue")
async def clear_queue(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    while not music_player.queue.empty():
        music_player.queue.get_nowait()
    
    embed = Embed(
        description=get_messages("clear_queue_success", guild_id),
        color=0xB5EAD7 if is_kawaii else discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# Commande /playnext
@bot.tree.command(name="playnext", description="Add a song to play next")
@app_commands.describe(query="Link or title of the video/song to play next")
async def play_next(interaction: discord.Interaction, query: str):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        embed = Embed(
            description=get_messages("no_voice_channel", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not music_player.voice_client or not music_player.voice_client.is_connected():
        try:
            music_player.voice_client = await interaction.user.voice.channel.connect()
        except Exception as e:
            embed = Embed(
                description=get_messages("connection_error", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"Error: {e}")
            return

    music_player.text_channel = interaction.channel
    await interaction.response.defer()

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "default_search": "ytsearch1",
        }
        info = await extract_info_async(ydl_opts, query)
        video = info["entries"][0] if "entries" in info else info
        video_url = video["webpage_url"]
        
        # Créer une nouvelle file d'attente
        new_queue = asyncio.Queue()
        await new_queue.put({'url': video_url, 'is_single': True})
        
        # Ajouter les chansons existantes
        while not music_player.queue.empty():
            item = await music_player.queue.get()
            await new_queue.put(item)
        
        music_player.queue = new_queue
        
        embed = Embed(
            title=get_messages("play_next_added", guild_id),
            description=f"[{video['title']}]({video['webpage_url']})",
            color=0xC7CEEA if is_kawaii else discord.Color.blue()
        )
        if video.get("thumbnail"):
            embed.set_thumbnail(url=video["thumbnail"])
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = Embed(
            description=get_messages("search_error", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"Error: {e}")

# Commande /nowplaying
@bot.tree.command(name="nowplaying", description="Show the current song playing")
async def now_playing(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.current_info:
        title = music_player.current_info.get("title", "Unknown Title")
        url = music_player.current_info.get("webpage_url", music_player.current_url)
        thumbnail = music_player.current_info.get("thumbnail")
        
        embed = Embed(
            title=get_messages("now_playing_title", guild_id),
            description=get_messages("now_playing_description", guild_id).format(title=title, url=url),
            color=0xC7CEEA if is_kawaii else discord.Color.green()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description=get_messages("no_song_playing", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def play_audio(guild_id):
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    while True:
        if music_player.queue.empty():
            if music_player.autoplay_enabled and music_player.last_was_single and music_player.current_url:
                # Envoyer le message d'autoplay immédiatement
                if music_player.text_channel:
                    embed = Embed(
                        description=get_messages("autoplay_added", guild_id),
                        color=0xC7CEEA if is_kawaii else discord.Color.blue()
                    )
                    await music_player.text_channel.send(embed=embed)
                
                # Ajouter des chansons similaires
                if "youtube.com" in music_player.current_url or "youtu.be" in music_player.current_url:
                    mix_playlist_url = get_mix_playlist_url(music_player.current_url)
                    if mix_playlist_url:
                        ydl_opts = {
                            "format": "bestaudio/best",
                            "quiet": True,
                            "no_warnings": True,
                            "extract_flat": True,
                        }
                        try:
                            info = await extract_info_async(ydl_opts, mix_playlist_url)
                            if "entries" in info:
                                current_video_id = get_video_id(music_player.current_url)
                                for entry in info["entries"]:
                                    entry_video_id = get_video_id(entry["url"])
                                    if entry_video_id and entry_video_id != current_video_id:
                                        await music_player.queue.put({'url': entry["url"], 'is_single': False})
                        except Exception as e:
                            print(f"Erreur YouTube Mix : {e}")
                elif "soundcloud.com" in music_player.current_url:
                    track_id = get_soundcloud_track_id(music_player.current_url)
                    if track_id:
                        station_url = get_soundcloud_station_url(track_id)
                        if station_url:
                            ydl_opts = {
                                "format": "bestaudio/best",
                                "quiet": True,
                                "no_warnings": True,
                                "extract_flat": True,
                            }
                            try:
                                info = await extract_info_async(ydl_opts, station_url)
                                if "entries" in info:
                                    current_track_id = track_id
                                    for entry in info["entries"]:
                                        entry_track_id = get_soundcloud_track_id(entry["url"])
                                        if entry_track_id and entry_track_id != current_track_id:
                                            await music_player.queue.put({'url': entry["url"], 'is_single': False})
                            except Exception as e:
                                print(f"Erreur SoundCloud Station : {e}")
            else:
                music_player.current_task = None
                music_player.current_info = None  # Réinitialiser les infos quand la file est vide
                break

        track_info = await music_player.queue.get()
        video_url = track_info['url']
        is_single = track_info['is_single']
        
        # Vérifier si c’est la dernière piste
        if music_player.queue.empty():
            music_player.last_was_single = is_single
        else:
            music_player.last_was_single = False
        
        music_player.current_url = video_url
        try:
            if not music_player.voice_client or not music_player.voice_client.is_connected():
                if music_player.text_channel:
                    await music_player.text_channel.guild.voice_client.disconnect()
                    music_player.voice_client = await music_player.text_channel.guild.voice_channels[0].connect()

            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
            }
            info = await extract_info_async(ydl_opts, video_url)
            music_player.current_info = info  # Stocker les infos de la chanson actuelle
            audio_url = info["url"]
            title = info.get("title", "Unknown Title")
            thumbnail = info.get("thumbnail")
            webpage_url = info.get("webpage_url", video_url)

            # Afficher "Now Playing" uniquement pour les pistes non uniques (playlists)
            if not is_single and music_player.text_channel:
                embed = Embed(
                    title=get_messages("now_playing_title", guild_id),
                    description=get_messages("now_playing_description", guild_id).format(
                        title=title,
                        url=webpage_url
                    ),
                    color=0xC7CEEA if is_kawaii else discord.Color.green()
                )
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)
                await music_player.text_channel.send(embed=embed)

            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn",
            }
            music_player.voice_client.play(
                discord.FFmpegPCMAudio(audio_url, **ffmpeg_options),
                after=lambda e: print(f"Erreur : {e}") if e else None
            )

            while music_player.voice_client.is_playing() or music_player.voice_client.is_paused():
                await asyncio.sleep(1)

            if music_player.loop_current:
                await music_player.queue.put({'url': video_url, 'is_single': is_single})
                continue

        except Exception as e:
            print(f"Erreur de lecture audio : {e}")
            continue

# Commande /pause
@bot.tree.command(name="pause", description="Pause the current playback")
async def pause(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.pause()
        embed = Embed(
            description=get_messages("pause", guild_id),
            color=0xFFB7B2 if is_kawaii else discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description=get_messages("no_playback", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /resume
@bot.tree.command(name="resume", description="Resume the playback")
async def resume(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.voice_client and music_player.voice_client.is_paused():
        music_player.voice_client.resume()
        embed = Embed(
            description=get_messages("resume", guild_id),
            color=0xB5EAD7 if is_kawaii else discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description=get_messages("no_paused", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /skip
@bot.tree.command(name="skip", description="Skip to the next song")
async def skip(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.stop()
        embed = Embed(
            description=get_messages("skip", guild_id),
            color=0xE2F0CB if is_kawaii else discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description=get_messages("no_song", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /loop
@bot.tree.command(name="loop", description="Enable/disable looping")
async def loop(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    music_player.loop_current = not music_player.loop_current
    state = get_messages("loop_state_enabled", guild_id) if music_player.loop_current else get_messages("loop_state_disabled", guild_id)
    
    embed = Embed(
        description=get_messages("loop", guild_id).format(state=state),
        color=0xC7CEEA if is_kawaii else discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# Commande /stop
@bot.tree.command(name="stop", description="Stop playback and disconnect the bot")
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.voice_client:
        if music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        while not music_player.queue.empty():
            music_player.queue.get_nowait()

        await music_player.voice_client.disconnect()
        music_player.voice_client = None
        music_player.current_task = None
        music_player.current_url = None
        music_player.current_info = None  # Réinitialiser les infos lors de l'arrêt

        embed = Embed(
            description=get_messages("stop", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description=get_messages("not_connected", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /shuffle
@bot.tree.command(name="shuffle", description="Shuffle the current queue")
async def shuffle(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if not music_player.queue.empty():
        items = []
        while not music_player.queue.empty():
            items.append(await music_player.queue.get())
        
        random.shuffle(items)
        
        music_player.queue = asyncio.Queue()
        for item in items:
            await music_player.queue.put(item)
        
        embed = Embed(
            description=get_messages("shuffle_success", guild_id),
            color=0xB5EAD7 if is_kawaii else discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description=get_messages("queue_empty", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /autoplay
@bot.tree.command(name="autoplay", description="Enable/disable autoplay of similar songs")
async def toggle_autoplay(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    music_player.autoplay_enabled = not music_player.autoplay_enabled
    state = get_messages("autoplay_state_enabled", guild_id) if music_player.autoplay_enabled else get_messages("autoplay_state_disabled", guild_id)
    
    embed = Embed(
        description=get_messages("autoplay_toggle", guild_id).format(state=state),
        color=0xC7CEEA if is_kawaii else discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is online.")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synchronized: {len(synced)}")

        async def rotate_presence():
            while True:
                if not bot.is_ready() or bot.is_closed():
                    return
                
                statuses = [
                    ("your Bandcamp links 🎶", discord.ActivityType.listening),
                    ("/play [link] 🔥", discord.ActivityType.listening),
                    (f"music on {len(bot.guilds)} servers 🎶", discord.ActivityType.playing)
                ]
                
                for status_text, status_type in statuses:
                    try:
                        await bot.change_presence(
                            activity=discord.Activity(
                                name=status_text,
                                type=status_type
                            )
                        )
                        await asyncio.sleep(10)
                    except Exception as e:
                        print(f"Status change error: {e}")
                        await asyncio.sleep(5)

        bot.loop.create_task(rotate_presence())
        
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Lancer le bot
bot.run("TOKEN")
