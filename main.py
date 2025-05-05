import discord
from discord.ext import commands
from discord import app_commands, Embed
import asyncio
import yt_dlp
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Intents pour le bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
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

# Stockage des informations de lecture
class MusicPlayer:
    def __init__(self):
        self.voice_client = None
        self.current_task = None
        self.queue = asyncio.Queue()
        self.current_url = None
        self.text_channel = None
        self.loop_current = False

music_player = MusicPlayer()

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
        print(f"Erreur Spotify: {e}")
        embed = Embed(
            description="Erreur lors du traitement du lien Spotify.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return None

# Commande /play originale avec ajout Spotify et SoundCloud
@bot.tree.command(name="play", description="Joue un lien ou recherche un titre sur YouTube/Spotify/SoundCloud.")
@app_commands.describe(query="Lien ou titre de la vidéo/musique à jouer")
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        embed = Embed(
            description="Tu dois être dans un salon vocal pour utiliser cette commande.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not music_player.voice_client or not music_player.voice_client.is_connected():
        try:
            music_player.voice_client = await interaction.user.voice.channel.connect()
        except Exception as e:
            embed = Embed(
                description="Erreur lors de la connexion au salon vocal.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"Erreur : {e}")
            return

    music_player.text_channel = interaction.channel
    await interaction.response.defer()

    # Vérifie si c'est un lien Spotify
    spotify_regex = re.compile(r'^(https?://)?(open\.spotify\.com)/.+$')
    if spotify_regex.match(query):
        spotify_queries = await process_spotify_url(query, interaction)
        if not spotify_queries:
            return

        if len(spotify_queries) > 1:
            embed = Embed(
                title="🎶 Playlist Spotify ajoutée",
                description=f"**{len(spotify_queries)} titres** en cours d'ajout...",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)

        for spotify_query in spotify_queries:
            try:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "default_search": "ytsearch1",
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(spotify_query, download=False)
                    video = info["entries"][0] if "entries" in info else info
                    await music_player.queue.put((video["url"], False))
                    
                    if len(spotify_queries) == 1:
                        embed = Embed(
                            title="🎵 Ajouté à la file d'attente",
                            description=f"[{video['title']}]({video['webpage_url']})",
                            color=discord.Color.blue()
                        )
                        embed.set_thumbnail(url=video["thumbnail"])
                        await interaction.followup.send(embed=embed)
            except Exception as e:
                print(f"Erreur conversion Spotify: {e}")
                continue
    else:
        # Vérifie si c'est un lien SoundCloud
        soundcloud_regex = re.compile(r'^(https?://)?(www\.)?(soundcloud\.com)/.+$')
        is_soundcloud = soundcloud_regex.match(query)
        
        # Vérifie si c'est un lien YouTube
        youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
        is_youtube = youtube_regex.match(query)
        
        if is_soundcloud or is_youtube:
            try:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": "in_playlist",
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                    
                    # Gestion des playlists
                    if "entries" in info:
                        for entry in info["entries"]:
                            if entry:  # Vérifie que l'entrée n'est pas None
                                await music_player.queue.put((entry["url"], True))

                        if info["entries"] and info["entries"][0]:  # Vérifie que la première entrée existe
                            thumbnail = info["entries"][0].get("thumbnail")
                            embed = Embed(
                                title="🎶 Playlist ajoutée",
                                description=f"**{len(info['entries'])} titres** ont été ajoutés à la file d'attente.",
                                color=discord.Color.green()
                            )
                            if thumbnail:
                                embed.set_thumbnail(url=thumbnail)
                            await interaction.followup.send(embed=embed)
                    else:
                        # Gestion des singles
                        await music_player.queue.put((info["url"], False))
                        embed = Embed(
                            title="🎵 Ajouté à la file d'attente",
                            description=f"[{info['title']}]({info['webpage_url']})",
                            color=discord.Color.blue()
                        )
                        if info.get("thumbnail"):
                            embed.set_thumbnail(url=info["thumbnail"])
                        await interaction.followup.send(embed=embed)
            except Exception as e:
                embed = Embed(
                    description="Erreur lors de l'ajout de la vidéo ou de la playlist.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                print(f"Erreur : {e}")
        else:
            # Recherche YouTube par défaut
            try:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "default_search": "ytsearch1",
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                    video = info["entries"][0] if "entries" in info else info
                    await music_player.queue.put((video["url"], False))
                    embed = Embed(
                        title="🎵 Ajouté à la file d'attente",
                        description=f"[{video['title']}]({video['webpage_url']})",
                        color=discord.Color.blue()
                    )
                    if video.get("thumbnail"):
                        embed.set_thumbnail(url=video["thumbnail"])
                    await interaction.followup.send(embed=embed)
            except Exception as e:
                embed = Embed(
                    description="Erreur lors de la recherche. Réessaie avec un autre titre.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                print(f"Erreur : {e}")

    if not music_player.current_task or music_player.current_task.done():
        music_player.current_task = asyncio.create_task(play_audio())

# Fonction pour lire l'audio
async def play_audio():
    while True:
        if music_player.queue.empty():
            music_player.current_task = None
            break

        url, is_playlist = await music_player.queue.get()
        try:
            if not music_player.voice_client or not music_player.voice_client.is_connected():
                if music_player.text_channel:
                    await music_player.text_channel.guild.voice_client.disconnect()
                    music_player.voice_client = await music_player.text_channel.guild.voice_channels[0].connect()

            music_player.current_url = url
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']

                if is_playlist and music_player.text_channel:
                    embed = Embed(
                        title="🎵 En cours de lecture",
                        description=f"[{info.get('title', 'Titre inconnu')}]({info.get('webpage_url', url)})",
                        color=discord.Color.green()
                    )
                    if info.get('thumbnail'):
                        embed.set_thumbnail(url=info['thumbnail'])
                    await music_player.text_channel.send(embed=embed)

                ffmpeg_options = {
                    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    "options": "-vn",
                }
                music_player.voice_client.play(
                    discord.FFmpegPCMAudio(audio_url, **ffmpeg_options),
                    after=lambda e: print(f"Erreur: {e}") if e else None
                )

                while music_player.voice_client.is_playing() or music_player.voice_client.is_paused():
                    await asyncio.sleep(1)

                if music_player.loop_current:
                    await music_player.queue.put((url, is_playlist))
                    continue

        except Exception as e:
            print(f"Erreur lecture audio: {e}")
            continue

# Commandes
@bot.tree.command(name="pause", description="Met en pause la lecture en cours.")
async def pause(interaction: discord.Interaction):
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.pause()
        embed = Embed(
            description="⏸️ Lecture mise en pause.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description="Aucune lecture en cours.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="resume", description="Reprend la lecture mise en pause.")
async def resume(interaction: discord.Interaction):
    if music_player.voice_client and music_player.voice_client.is_paused():
        music_player.voice_client.resume()
        embed = Embed(
            description="▶️ Lecture reprise.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description="Aucune lecture mise en pause.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="skip", description="Passe à la chanson suivante.")
async def skip(interaction: discord.Interaction):
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.stop()
        embed = Embed(
            description="⏭️ Chanson actuelle ignorée.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description="Aucune chanson en cours.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="loop", description="Active ou désactive la lecture en boucle pour la musique actuelle.")
async def loop(interaction: discord.Interaction):
    music_player.loop_current = not music_player.loop_current
    state = "activée" if music_player.loop_current else "désactivée"
    embed = Embed(
        description=f"🔁 Lecture en boucle pour la musique actuelle {state}.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stop", description="Arrête la lecture et déconnecte le bot.")
async def stop(interaction: discord.Interaction):
    if music_player.voice_client:
        if music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        while not music_player.queue.empty():
            music_player.queue.get_nowait()

        await music_player.voice_client.disconnect()
        music_player.voice_client = None
        music_player.current_task = None
        music_player.current_url = None

        embed = Embed(
            description="⏹️ Lecture arrêtée et bot déconnecté.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            description="Le bot n'est pas connecté à un salon vocal.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f"{bot.user.name} est en ligne.")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")

        async def rotate_presence():
            statuses = [
                "vos liens Spotify 🎧",
                "/play [lien] 🔥",
            ]
            
            while True:
                try:
                    for status in statuses:
                        # Vérifie que la connexion est toujours active
                        if not bot.is_ready() or bot.is_closed():
                            return
                            
                        try:
                            await bot.change_presence(
                                activity=discord.Activity(
                                    name=status,
                                    type=discord.ActivityType.listening
                                )
                            )
                        except (discord.ConnectionClosed, discord.HTTPException) as e:
                            print(f"Erreur changement statut (réessai dans 5s): {type(e).__name__}")
                            await asyncio.sleep(5)
                            continue
                            
                        await asyncio.sleep(5)  # Intervalle de 5 secondes
                        
                except Exception as e:
                    print(f"Erreur inattendue (rotation continuée): {type(e).__name__}: {e}")
                    await asyncio.sleep(5)

        # Démarrer la tâche avec une gestion d'erreur supplémentaire
        def start_task():
            task = bot.loop.create_task(rotate_presence())
            def restart_if_failed(fut):
                try:
                    fut.result()  # Vérifie s'il y a eu une exception
                except Exception as e:
                    print(f"Tâche de rotation crashée, redémarrage: {e}")
                    start_task()  # Relance la tâche
                    
            task.add_done_callback(restart_if_failed)
            
        start_task()
        
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")
        
bot.run("TON_TOKEN")
