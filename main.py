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
from cachetools import TTLCache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Intents for the bot
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

# Create the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Spotify configuration
SPOTIFY_CLIENT_ID = 'CLIENTIDHERE'
SPOTIFY_CLIENT_SECRET = 'CLIENTSECRETHERE'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    requests_timeout=15
))

# Cache for YouTube searches (2-hour TTL, size for 500+ servers)
url_cache = TTLCache(maxsize=75000, ttl=7200)

# Normalize strings for search queries
def sanitize_query(query):
    query = re.sub(r'[\x00-\x1F\x7F]', '', query)  # Remove control chars
    query = re.sub(r'\s+', ' ', query).strip()  # Normalize spaces
    return query

# Retry Spotify API calls with backoff
async def retry_spotify_call(func, *args, max_retries=3, backoff_factor=1.5, **kwargs):
    for attempt in range(max_retries):
        try:
            return await asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs))
        except spotipy.exceptions.SpotifyException as se:
            if se.http_status in [400, 401, 404, 429]:
                if attempt == max_retries - 1:
                    raise
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"Spotify API error {se.http_status}: {se.msg}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise
        except Exception as e:
            logger.error(f"Unexpected error in Spotify call: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(backoff_factor)
    raise Exception("Max retries reached for Spotify API call")

# Async yt-dlp info extraction
async def extract_info_async(ydl_opts, query, loop=None):
    if loop is None:
        loop = asyncio.get_running_loop()
    
    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)
    
    return await loop.run_in_executor(None, extract)

# Create loading bar
def create_loading_bar(progress, width=10):
    filled = int(progress * width)
    unfilled = width - filled
    return '```[' + '█' * filled + '░' * unfilled + '] ' + f'{int(progress * 100)}%```'

# Music player state
class MusicPlayer:
    def __init__(self):
        self.voice_client = None
        self.current_task = None
        self.queue = asyncio.Queue()
        self.current_url = None
        self.current_info = None
        self.text_channel = None
        self.loop_current = False
        self.autoplay_enabled = False
        self.last_was_single = False

# Server states
music_players = {}  # {guild_id: MusicPlayer()}
kawaii_mode = {}    # {guild_id: bool}
server_languages = {}  # {guild_id: "en" or "fr"}

# Get player for a server
def get_player(guild_id):
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer()
    return music_players[guild_id]

# Get kawaii mode
def get_mode(guild_id):
    return kawaii_mode.get(guild_id, False)

# Get language
def get_language(guild_id):
    return server_languages.get(guild_id, "en")

# Messages based on language and kawaii mode
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
                "normal": "Error processing the Spotify link. It may be private, region-locked, or invalid.",
                "kawaii": "(´；ω；`) Oh no! Problem with the Spotify link... maybe it’s shy or hidden?"
            },
            "spotify_playlist_added": {
                "normal": "🎶 Spotify Playlist Added",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ SPOTIFY PLAYLIST"
            },
            "spotify_playlist_description": {
                "normal": "**{count} tracks** added, {failed} failed.\n{failed_tracks}",
                "kawaii": "**{count} songs** added, {failed} couldn’t join! (´･ω･`)\n{failed_tracks}"
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
                "normal": "🎵 Adding similar songs to the queue... (This may take up to 1 minute)",
                "kawaii": "♪(´▽｀) Adding similar songs to the queue! ~ (It might take a little while!)"
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
            "loading_playlist": {
                "normal": "Processing playlist...\n{processed}/{total} tracks added",
                "kawaii": "(✿◕‿◕) Processing playlist...\n{processed}/{total} songs added"
            },
            "playlist_error": {
                "normal": "Error processing the playlist. It may be private, region-locked, or invalid.",
                "kawaii": "(´；ω；`) Oh no! Problem with the playlist... maybe it’s shy or hidden?"
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
                "normal": "Erreur lors du traitement du lien Spotify. Il peut être privé, restreint à une région ou invalide.",
                "kawaii": "(´；ω；`) Oh non ! Problème avec le lien Spotify... peut-être qu’il est timide ou caché ?"
            },
            "spotify_playlist_added": {
                "normal": "🎶 Playlist Spotify ajoutée",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ PLAYLIST SPOTIFY"
            },
            "spotify_playlist_description": {
                "normal": "**{count} chansons** ajoutées, {failed} échouées.\n{failed_tracks}",
                "kawaii": "**{count} chansons** ajoutées, {failed} n’ont pas pu rejoindre ! (´･ω･`)\n{failed_tracks}"
            },
            "song_added": {
                "normal": "🎵 Ajoutée à la file",
                "kawaii": "(っ◕‿◕)っ ♫ MUSIQUE AJOUTÉE ♫"
            },
            "playlist_added": {
                "normal": "🎶 Playlist ajoutée",
                "kawaii": "✧･ﾟ: *✧･ﾟ:* PLAYLIST *:･ﾟ✧*:･ﾟ✧"
            },
            "playlist_description": {
                "normal": "**{count} chansons** ajoutées à la file d'attente.",
                "kawaii": "**{count} musiques** ajoutées !"
            },
            "ytmusic_playlist_added": {
                "normal": "🎶 Playlist YouTube Music ajoutée",
                "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ PLAYLIST YOUTUBE MUSIC"
            },
            "ytmusic_playlist_description": {
                "normal": "**{count} chansons** en cours d'ajout...",
                "kawaii": "**{count} musiques** ajoutées !"
            },
            "video_error": {
                "normal": "Erreur lors de l'ajout de la vidéo ou de la playlist.",
                "kawaii": "(´；ω；`) Problème avec cette vidéo..."
            },
            "search_error": {
                "normal": "Erreur lors de la recherche. Essaye un autre titre.",
                "kawaii": "(¨_°`) Je n'ai pas trouvé cette musique..."
            },
            "now_playing_title": {
                "normal": "🎶 En cours de lecture",
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
                "kawaii": "désactivée (¨_°`)"
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
                "normal": "🎶 Ajout de chansons similaires à la file... (Cela peut prendre jusqu'à 1 minute)",
                "kawaii": "♪(´▽｀) Ajout de chansons similaires à la file ! ~ (Ça peut prendre un petit moment !)"
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
            "loading_playlist": {
                "normal": "Traitement de la playlist...\n{processed}/{total} chansons ajoutées",
                "kawaii": "(✿◕‿◕) Traitement de la playlist...\n{processed}/{total} musiques ajoutées"
            },
            "playlist_error": {
                "normal": "Erreur lors du traitement de la playlist. Elle peut être privée, restreinte à une région ou invalide.",
                "kawaii": "(´；ω；`) Oh non ! Problème avec la playlist... peut-être qu’elle est timide ou cachée ?"
            },
        }
    }
    
    mode = "kawaii" if is_kawaii else "normal"
    return messages[lang][message_key][mode]

# YouTube Mix and SoundCloud Stations utilities
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

# Process Spotify URLs
async def process_spotify_url(url, interaction):
    try:
        parsed_url = urlparse(url)
        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        resource_id = clean_url.split('/')[-1].split('?')[0]
        logger.info(f"Processing Spotify URL: {clean_url} (ID: {resource_id})")

        sp.auth_manager.get_access_token(as_dict=False)

        if 'playlist' in clean_url:
            try:
                playlist_info = await retry_spotify_call(sp.playlist, resource_id)
                logger.info(f"Playlist found: {playlist_info.get('name', 'Unknown')} (Public: {playlist_info.get('public', False)})")
                
                if not playlist_info['public']:
                    embed = Embed(
                        description="⚠️ Cette playlist est privée ou inaccessible.",
                        color=0xFFB6C1 if get_mode(interaction.guild_id) else discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return None
                
                total_tracks = playlist_info['tracks']['total']
                logger.info(f"Total tracks in playlist: {total_tracks}")
                
                if total_tracks == 0:
                    embed = Embed(
                        description="⚠️ La playlist est vide.",
                        color=0xFFB6C1 if get_mode(interaction.guild_id) else discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return None
                
                tracks = []
                offset = 0
                limit = 100

                while offset < total_tracks:
                    try:
                        results = await retry_spotify_call(
                            sp.playlist_tracks,
                            resource_id,
                            limit=limit,
                            offset=offset,
                            fields="items(track(name,artists(name)))"
                        )
                        tracks.extend([item['track'] for item in results['items'] if item['track']])
                        offset += limit
                        await asyncio.sleep(0.2)
                        logger.info(f"Fetched {len(tracks)}/{total_tracks} tracks from playlist {resource_id}")
                    except spotipy.exceptions.SpotifyException:
                        results = await retry_spotify_call(
                            sp.playlist_tracks,
                            resource_id,
                            limit=limit,
                            offset=offset,
                            fields="items(track(name,artists(name)))",
                            market="US"
                        )
                        tracks.extend([item['track'] for item in results['items'] if item['track']])
                        offset += limit
                        await asyncio.sleep(0.2)
                
                if not tracks:
                    embed = Embed(
                        description="⚠️ Aucune piste valide trouvée dans la playlist.",
                        color=0xFFB6C1 if get_mode(interaction.guild_id) else discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return None
                
                return [(track['name'], track['artists'][0]['name']) for track in tracks]
            
            except spotipy.exceptions.SpotifyException as se:
                logger.error(f"Erreur de validation Spotify pour playlist {resource_id}: {se}")
                try:
                    playlist_info = await retry_spotify_call(sp.playlist, resource_id, market="US")
                    total_tracks = playlist_info['tracks']['total']
                    tracks = []
                    offset = 0
                    limit = 100
                    while offset < total_tracks:
                        results = await retry_spotify_call(
                            sp.playlist_tracks,
                            resource_id,
                            limit=limit,
                            offset=offset,
                            market="US"
                        )
                        tracks.extend([item['track'] for item in results['items'] if item['track']])
                        offset += limit
                        await asyncio.sleep(0.2)
                    return [(track['name'], track['artists'][0]['name']) for track in tracks]
                except spotipy.exceptions.SpotifyException as se_fallback:
                    logger.error(f"Fallback failed for playlist {resource_id}: {se_fallback}")
                    embed = Embed(
                        description=get_messages("spotify_error", interaction.guild_id),
                        color=0xFFB6C1 if get_mode(interaction.guild_id) else discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return None
        elif 'track' in clean_url:
            track = await retry_spotify_call(sp.track, resource_id)
            return [(track['name'], track['artists'][0]['name'])]
        elif 'album' in clean_url:
            results = await retry_spotify_call(sp.album_tracks, resource_id, limit=50)
            tracks = results['items']
            while results['next']:
                results = await retry_spotify_call(sp.next, results)
                tracks.extend(results['items'])
                await asyncio.sleep(0.2)
            return [(item['name'], item['artists'][0]['name']) for item in tracks]
        elif 'artist' in clean_url:
            results = await retry_spotify_call(sp.artist_top_tracks, resource_id)
            return [(track['name'], track['artists'][0]['name']) for track in results['tracks']]
    except spotipy.exceptions.SpotifyException as se:
        logger.error(f"Erreur Spotify globale : {se}")
        embed = Embed(
            description=f"Erreur Spotify : {se.http_status} - {se.msg}",
            color=0xFFB6C1 if get_mode(interaction.guild_id) else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")
        embed = Embed(
            description=get_messages("spotify_error", interaction.guild_id),
            color=0xFFB6C1 if get_mode(interaction.guild_id) else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return None

# /kaomoji command
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

# /language command
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
            logger.error(f"Error: {e}")
            return

    music_player.text_channel = interaction.channel
    await interaction.response.defer()

    spotify_regex = re.compile(r'^(https?://)?(open\.spotify\.com)/.+$')
    soundcloud_regex = re.compile(r'^(https?://)?(www\.)?(soundcloud\.com)/.+$')
    youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
    ytmusic_regex = re.compile(r'^(https?://)?(music\.youtube\.com)/.+$')
    bandcamp_regex = re.compile(r'^(https?://)?([^\.]+)\.bandcamp\.com/.+$')
    
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "noplaylist": True,
        "no_color": True,
        "socket_timeout": 10,
        "force_generic_extractor": True,
    }

    async def search_track(track):
        track_name, artist_name = track
        original_query = f"{track_name} {artist_name}"
        sanitized_query = sanitize_query(original_query)
        cache_key = sanitized_query.lower()
        logger.info(f"Searching YouTube for: {original_query} (Sanitized: {sanitized_query})")
        
        try:
            if cache_key in url_cache:
                logger.info(f"Cache hit for {cache_key}")
                return cache_key, url_cache[cache_key], track_name, artist_name
            
            ydl_opts_search = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "noplaylist": True,
                "no_color": True,
                "socket_timeout": 10,
            }
            
            # Explicitly force search with "ytsearch:" prefix
            search_query = f"ytsearch:{sanitized_query}"
            info = await extract_info_async(ydl_opts_search, search_query)
            
            if "entries" in info and info["entries"]:
                for entry in info["entries"][:3]:  # Check top 3 results
                    try:
                        video_url = entry["url"]
                        video_title = entry.get("title", "Unknown Title")
                        logger.info(f"Found YouTube URL: {video_url} (Title: {video_title})")
                        url_cache[cache_key] = video_url
                        return cache_key, video_url, track_name, artist_name
                    except Exception as e:
                        logger.warning(f"Skipping unavailable video for {sanitized_query}: {e}")
                        continue
                logger.warning(f"No accessible videos in top results for {sanitized_query}")
            
            # Fallback to track title only
            sanitized_track = sanitize_query(track_name)
            logger.info(f"Fallback search: {sanitized_track}")
            search_query = f"ytsearch:{sanitized_track}"
            info = await extract_info_async(ydl_opts_search, search_query)
            if "entries" in info and info["entries"]:
                for entry in info["entries"][:3]:
                    try:
                        video_url = entry["url"]
                        video_title = entry.get("title", "Unknown Title")
                        logger.info(f"Found YouTube URL: {video_url} (Title: {video_title})")
                        url_cache[cache_key] = video_url
                        return cache_key, video_url, track_name, artist_name
                    except Exception as e:
                        logger.warning(f"Skipping unavailable video for {sanitized_track}: {e}")
                        continue
                logger.warning(f"No accessible videos in top results for {sanitized_track}")
            
            # Fallback to artist only
            sanitized_artist = sanitize_query(artist_name)
            logger.info(f"Fallback search: {sanitized_artist}")
            search_query = f"ytsearch:{sanitized_artist}"
            info = await extract_info_async(ydl_opts_search, search_query)
            if "entries" in info and info["entries"]:
                for entry in info["entries"][:3]:
                    try:
                        video_url = entry["url"]
                        video_title = entry.get("title", "Unknown Title")
                        logger.info(f"Found YouTube URL: {video_url} (Title: {video_title})")
                        url_cache[cache_key] = video_url
                        return cache_key, video_url, track_name, artist_name
                    except Exception as e:
                        logger.warning(f"Skipping unavailable video for {sanitized_artist}: {e}")
                        continue
                logger.warning(f"No accessible videos in top results for {sanitized_artist}")
            
            # No results found
            logger.warning(f"No YouTube results for {sanitized_query}, {sanitized_track}, or {sanitized_artist}")
            url_cache[cache_key] = None
            return cache_key, None, track_name, artist_name
        
        except Exception as e:
            logger.error(f"Failed to search YouTube for {sanitized_query}: {e}")
            url_cache[cache_key] = None
            return cache_key, None, track_name, artist_name

    if spotify_regex.match(query):
        spotify_tracks = await process_spotify_url(query, interaction)
        if not spotify_tracks:
            return

        if len(spotify_tracks) == 1:
            track_name, artist_name = spotify_tracks[0]
            query = f"{track_name} {artist_name}"
            try:
                cache_key = sanitize_query(query).lower()
                # Utiliser des options spécifiques pour récupérer la miniature
                ydl_opts_full = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "no_color": True,
                    "socket_timeout": 10,
                    "force_generic_extractor": True,
                }
                sanitized_query = sanitize_query(query)
                search_query = f"ytsearch:{sanitized_query}"
                info = await extract_info_async(ydl_opts_full, search_query)
                video = info["entries"][0] if "entries" in info and info["entries"] else None
                if not video:
                    raise Exception("No results found")
                video_url = video.get("webpage_url", video.get("url"))
                if not video_url:
                    raise KeyError("No valid URL found in video metadata")
                logger.debug(f"Metadata for single track: {video}")
                url_cache[cache_key] = video_url
                await music_player.queue.put({'url': video_url, 'is_single': True})
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{video.get('title', track_name)}]({video_url})",
                    color=0xC7CEEA if is_kawaii else discord.Color.blue()
                )
                if video.get("thumbnail"):
                    embed.set_thumbnail(url=video["thumbnail"])
                if is_kawaii:
                    embed.set_footer(text="☆⌒(≧▽° )")
                await interaction.followup.send(embed=embed)
            except Exception as e:
                logger.error(f"Erreur de conversion Spotify pour {query}: {e}")
                embed = Embed(
                    description=get_messages("search_error", guild_id),
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Send initial processing message
            embed = Embed(
                title=f"Processing Spotify Playlist",
                description="Starting...",
                color=0xFFB6C1 if is_kawaii else discord.Color.blue()
            )
            message = await interaction.followup.send(embed=embed)
            
            total_tracks = len(spotify_tracks)
            processed = 0
            failed = 0
            failed_tracks = []
            batch_size = 50
            
            for i in range(0, total_tracks, batch_size):
                batch = spotify_tracks[i:i + batch_size]
                tasks = [search_track(track) for track in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception) or result[1] is None:
                        failed += 1
                        if len(failed_tracks) < 5:
                            failed_tracks.append(f"{result[2]} by {result[3]}")
                    else:
                        _, video_url, _, _ = result
                        await music_player.queue.put({'url': video_url, 'is_single': False})
                    processed += 1
                    
                    # Update progress every 10 tracks or at the end
                    if processed % 10 == 0 or processed == total_tracks:
                        progress = processed / total_tracks
                        bar = create_loading_bar(progress)
                        description = f"{bar}\n" + get_messages("loading_playlist", guild_id).format(
                            processed=processed,
                            total=total_tracks
                        )
                        embed.description = description
                        await message.edit(embed=embed)
                await asyncio.sleep(0.1)
            
            logger.info(f"Playlist processed: {processed - failed} tracks added, {failed} failed")
            
            if processed - failed == 0:
                embed = Embed(
                    description="⚠️ Aucune piste n'a pu être ajoutée.",
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                await message.edit(embed=embed)
                return

            failed_text = "\nFailed tracks (up to 5):\n" + "\n".join([f"- {track}" for track in failed_tracks]) if failed_tracks else ""
            embed.title = get_messages("spotify_playlist_added", guild_id)
            embed.description = get_messages("spotify_playlist_description", guild_id).format(
                count=processed - failed,
                failed=failed,
                failed_tracks=failed_text
            )
            embed.color = 0xB5EAD7 if is_kawaii else discord.Color.green()
            await message.edit(embed=embed)
    elif soundcloud_regex.match(query) or youtube_regex.match(query) or ytmusic_regex.match(query) or bandcamp_regex.match(query):
        try:
            # Déterminer la plateforme
            platform = ""
            if soundcloud_regex.match(query):
                platform = "SoundCloud"
            elif ytmusic_regex.match(query):
                platform = "YouTube Music"
            elif youtube_regex.match(query):
                platform = "YouTube"
            elif bandcamp_regex.match(query):
                platform = "Bandcamp"
                
            ydl_opts_playlist = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": "in_playlist",
                "noplaylist": False,
                "no_color": True,
                "socket_timeout": 10,
                "force_generic_extractor": True,
            }
            info = await extract_info_async(ydl_opts_playlist, query)
            
            if "entries" in info:
                total_tracks = len(info["entries"])
                processed = 0
                    
                # Create initial embed
                embed = Embed(
                    title=f"Processing {platform} Playlist",
                    description=get_messages("loading_playlist", guild_id).format(processed=0, total=total_tracks),
                    color=0xFFB6C1 if is_kawaii else discord.Color.blue()
                )
                message = await interaction.followup.send(embed=embed)
                for entry in info["entries"]:
                    if entry:
                        await music_player.queue.put({'url': entry['url'], 'is_single': False})
                        processed += 1
                        
                        # Update progress every 10 tracks or at the end
                        if processed % 10 == 0 or processed == total_tracks:
                            progress = processed / total_tracks
                            bar = create_loading_bar(progress)
                            new_description = f"{bar}\n" + get_messages("loading_playlist", guild_id).format(
                                processed=processed, 
                                total=total_tracks
                            )
                            embed.description = new_description
                            await message.edit(embed=embed)
                
                # Final success message
                if info["entries"] and info["entries"][0]:
                    thumbnail = info["entries"][0].get("thumbnail")
                    embed.title = get_messages("ytmusic_playlist_added", guild_id) if ytmusic_regex.match(query) else get_messages("playlist_added", guild_id)
                    embed.description = get_messages("ytmusic_playlist_description", guild_id).format(count=total_tracks) if ytmusic_regex.match(query) else get_messages("playlist_description", guild_id).format(count=total_tracks)
                    embed.color = 0xE2F0CB if is_kawaii else discord.Color.green()
                    if thumbnail:
                        embed.set_thumbnail(url=thumbnail)
                    await message.edit(embed=embed)
            else:
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
            logger.error(f"Error: {e}")
    else:
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "noplaylist": True,
                "no_color": True,
                "socket_timeout": 10,
                "force_generic_extractor": True,
            }
            # Ajouter le préfixe ytsearch: si la requête n'est pas une URL
            sanitized_query = sanitize_query(query)
            search_query = f"ytsearch:{sanitized_query}"
            info = await extract_info_async(ydl_opts, search_query)
            video = info["entries"][0] if "entries" in info and info["entries"] else None
            if not video:
                raise Exception("No results found")
            video_url = video.get("webpage_url", video.get("url"))
            if not video_url:
                raise KeyError("No valid URL found in video metadata")
            
            await music_player.queue.put({'url': video_url, 'is_single': True})
            
            embed = Embed(
                title=get_messages("song_added", guild_id),
                description=f"[{video.get('title', 'Unknown Title')}]({video_url})",
                color=0xB5EAD7 if is_kawaii else discord.Color.blue()
            )
            if video.get("thumbnail"):
                embed.set_thumbnail(url=video["thumbnail"])
            if is_kawaii:
                embed.set_footer(text="☆⌒(≧▽° )")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = Embed(
                description=get_messages("search_error", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.error(f"Error searching for {query}: {e}")

    if not music_player.current_task or music_player.current_task.done():
        music_player.current_task = asyncio.create_task(play_audio(guild_id))
                                
# /queue command
@bot.tree.command(name="queue", description="Show the current queue")
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.queue.qsize() == 0:
        embed = Embed(
            description=get_messages("queue_empty", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    queue_items = list(music_player.queue._queue)[:5]
    next_songs = []
    for item in queue_items:
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "force_generic_extractor": True,
            }
            info = await extract_info_async(ydl_opts, item['url'])
            title = info.get("title", "Unknown Title")
            url = info.get("webpage_url", item['url'])
            next_songs.append(get_messages("queue_song", guild_id).format(title=title, url=url))
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des infos : {e}")
            next_songs.append("- Chanson inconnue")
    
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
    
    await interaction.followup.send(embed=embed)

# /clearqueue command
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
            logger.error(f"Error: {e}")
            return

    music_player.text_channel = interaction.channel
    await interaction.response.defer()

    spotify_regex = re.compile(r'^(https?://)?(open\.spotify\.com)/.+$')

    try:
        if spotify_regex.match(query):
            spotify_tracks = await process_spotify_url(query, interaction)
            if not spotify_tracks or len(spotify_tracks) != 1:
                raise Exception("Only single Spotify tracks are supported for /playnext")
            
            track_name, artist_name = spotify_tracks[0]
            search_query = f"ytsearch:{sanitize_query(f'{track_name} {artist_name}')}"
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "no_color": True,
                "socket_timeout": 10,
                "force_generic_extractor": True,
            }
            info = await extract_info_async(ydl_opts, search_query)
            video = info["entries"][0] if "entries" in info and info["entries"] else None
            if not video:
                raise Exception("No results found")
            video_url = video.get("webpage_url", video.get("url"))
            if not video_url:
                raise KeyError("No valid URL found in video metadata")
            
            logger.debug(f"Metadata for Spotify track: {video}")
        else:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "noplaylist": True,
                "no_color": True,
                "socket_timeout": 10,
                "force_generic_extractor": True,
            }
            search_query = f"ytsearch:{sanitize_query(query)}" if not query.startswith(('http://', 'https://')) else query
            info = await extract_info_async(ydl_opts, search_query)
            video = info["entries"][0] if "entries" in info and info["entries"] else info
            video_url = video.get("webpage_url", video.get("url"))
            if not video_url:
                raise KeyError("No valid URL found in video metadata")
            
            logger.debug(f"Metadata for non-Spotify query: {video}")

        new_queue = asyncio.Queue()
        await new_queue.put({'url': video_url, 'is_single': True})
        
        while not music_player.queue.empty():
            item = await music_player.queue.get()
            await new_queue.put(item)
        
        music_player.queue = new_queue
        
        embed = Embed(
            title=get_messages("play_next_added", guild_id),
            description=f"[{video.get('title', 'Unknown Title')}]({video_url})",
            color=0xC7CEEA if is_kawaii else discord.Color.blue()
        )
        if video.get("thumbnail"):
            embed.set_thumbnail(url=video["thumbnail"])
        if is_kawaii:
            embed.set_footer(text="☆⌒(≧▽° )")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = Embed(
            description=get_messages("search_error", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.error(f"Error processing /playnext for {query}: {e}")
        
# /nowplaying command
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

# Playback function
async def play_audio(guild_id):
    try:
        is_kawaii = get_mode(guild_id)
        music_player = get_player(guild_id)
        
        while True:
            if music_player.queue.qsize() == 0:
                if music_player.autoplay_enabled and music_player.last_was_single and music_player.current_url:
                    if music_player.text_channel:
                        embed = Embed(
                            description=get_messages("autoplay_added", guild_id),
                            color=0xFFB6C1 if is_kawaii else discord.Color.blue()
                        )
                        await music_player.text_channel.send(embed=embed)
                    
                    if "youtube.com" in music_player.current_url or "youtu.be" in music_player.current_url:
                        mix_playlist_url = get_mix_playlist_url(music_player.current_url)
                        if mix_playlist_url:
                            ydl_opts = {
                                "format": "bestaudio/best",
                                "quiet": True,
                                "no_warnings": True,
                                "extract_flat": True,
                                "no_color": True,
                                "socket_timeout": 10,
                                "force_generic_extractor": True,
                            }
                            try:
                                info = await extract_info_async(ydl_opts, mix_playlist_url)
                                if "entries" in info:
                                    current_video_id = get_video_id(music_player.current_url)
                                    for entry in info["entries"]:
                                        entry_video_id = get_video_id(entry["url"])
                                        if entry_video_id and entry_video_id != current_video_id:
                                            await music_player.queue.put({'url': entry["url"], 'is_single': True})
                            except Exception as e:
                                logger.error(f"Erreur YouTube Mix : {e}")
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
                                    "no_color": True,
                                    "socket_timeout": 10,
                                    "force_generic_extractor": True,
                                }
                                try:
                                    info = await extract_info_async(ydl_opts, station_url)
                                    if "entries" in info:
                                        current_track_id = track_id
                                        for entry in info["entries"]:
                                            entry_track_id = get_soundcloud_track_id(entry["url"])
                                            if entry_track_id and entry_track_id != current_track_id:
                                                await music_player.queue.put({'url': entry["url"], 'is_single': True})
                                except Exception as e:
                                    logger.error(f"Erreur SoundCloud Station : {e}")
                else:
                    music_player.current_task = None
                    music_player.current_info = None
                    break

            track_info = await music_player.queue.get()
            video_url = track_info['url']
            is_single = track_info['is_single']
            
            if music_player.queue.qsize() == 0:
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
                    "no_color": True,
                    "socket_timeout": 10,
                    "force_generic_extractor": True,
                }
                info = await extract_info_async(ydl_opts, video_url)
                music_player.current_info = info
                audio_url = info["url"]
                title = info.get("title", "Unknown Title")
                thumbnail = info.get("thumbnail")
                webpage_url = info.get("webpage_url", video_url)

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
                    after=lambda e: logger.error(f"Erreur : {e}") if e else None
                )

                while music_player.voice_client.is_playing() or music_player.voice_client.is_paused():
                    await asyncio.sleep(1)

                if music_player.loop_current:
                    await music_player.queue.put({'url': video_url, 'is_single': is_single})
                    continue

            except Exception as e:
                logger.error(f"Erreur de lecture audio pour {video_url}: {e}")
                continue

    except Exception as e:
        logger.error(f"Erreur dans play_audio pour guild {guild_id}: {e}")

# /pause command
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

# /resume command
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

# /skip command
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

# /loop command
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

# /stop command
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
        music_player.current_info = None

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

# /shuffle command
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

# /autoplay command
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
    logger.info(f"{bot.user.name} is online.")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Slash commands synchronized: {len(synced)}")

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
                        logger.error(f"Status change error: {e}")
                        await asyncio.sleep(5)

        bot.loop.create_task(rotate_presence())
        
    except Exception as e:
        logger.error(f"Error syncing commands: {e}")

# Run the bot
bot.run("TOKEN")
