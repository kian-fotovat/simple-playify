import discord
from discord.ext import commands
from discord import app_commands, Embed
import asyncio
import yt_dlp
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import concurrent.futures

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

# Fonction asynchrone pour extraire les informations avec yt_dlp
async def extract_info_async(ydl_opts, query, loop=None):
    """Exécute yt_dlp.extract_info dans un thread séparé pour éviter de bloquer."""
    if loop is None:
        loop = asyncio.get_running_loop()
    
    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)
    
    return await loop.run_in_executor(None, extract)

# Stockage des informations de lecture et des modes par serveur
class MusicPlayer:
    def __init__(self):
        self.voice_client = None
        self.current_task = None
        self.queue = asyncio.Queue()
        self.current_url = None
        self.text_channel = None
        self.loop_current = False

# Dictionnaires pour stocker les états par serveur
music_players = {}  # {guild_id: MusicPlayer()}
kawaii_mode = {}    # {guild_id: bool}

# Fonction pour obtenir le player d'un serveur
def get_player(guild_id):
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer()
    return music_players[guild_id]

# Fonction pour obtenir le mode actuel d'un serveur
def get_mode(guild_id):
    return kawaii_mode.get(guild_id, False)

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
        if get_mode(interaction.guild_id):
            description = "(´；ω；`) Oh non ! Problème avec le lien Spotify..."
            color = 0xFFB6C1  # Rose pastel
        else:
            description = "Erreur lors du traitement du lien Spotify."
            color = discord.Color.red()
            
        embed = Embed(description=description, color=color)
        await interaction.followup.send(embed=embed, ephemeral=True)
        return None

# Commande pour basculer entre les modes
@bot.tree.command(name="kaomoji", description="Active/désactive le mode kaomoji")
@app_commands.default_permissions(administrator=True)
async def toggle_kawaii(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    kawaii_mode[guild_id] = not get_mode(guild_id)
    state = "activé (◕‿◕✿)" if kawaii_mode[guild_id] else "désactivé"
    
    embed = Embed(
        description=f"Mode kawaii {state} pour ce serveur !",
        color=0xFFB6C1 if kawaii_mode[guild_id] else discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /play avec gestion des deux modes
@bot.tree.command(name="play", description="Joue un lien ou recherche un titre")
@app_commands.describe(query="Lien ou titre de la vidéo/musique à jouer")
async def play(interaction: discord.Interaction, query: str):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        if is_kawaii:
            description = "(｡•́︿•̀｡) Tu dois être dans un salon vocal !"
            color = 0xFF9AA2
        else:
            description = "Tu dois être dans un salon vocal pour utiliser cette commande."
            color = discord.Color.red()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not music_player.voice_client or not music_player.voice_client.is_connected():
        try:
            music_player.voice_client = await interaction.user.voice.channel.connect()
        except Exception as e:
            if is_kawaii:
                description = "(╥﹏╥) Je n'ai pas pu me connecter..."
                color = 0xFF9AA2
            else:
                description = "Erreur lors de la connexion au salon vocal."
                color = discord.Color.red()
                
            embed = Embed(description=description, color=color)
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
            if is_kawaii:
                title = "☆*:.｡.o(≧▽≦)o.｡.:*☆ PLAYLIST SPOTIFY"
                description = f"**{len(spotify_queries)} musiques** ajoutées !"
                color = 0xB5EAD7
            else:
                title = "🎶 Playlist Spotify ajoutée"
                description = f"**{len(spotify_queries)} titres** en cours d'ajout..."
                color = discord.Color.green()
                
            embed = Embed(title=title, description=description, color=color)
            await interaction.followup.send(embed=embed)

        for spotify_query in spotify_queries:
            try:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "default_search": "ytsearch1",
                }
                info = await extract_info_async(ydl_opts, spotify_query)
                video = info["entries"][0] if "entries" in info else info
                await music_player.queue.put((video["url"], False))
                
                if len(spotify_queries) == 1:
                    if is_kawaii:
                        title = "(っ◕‿◕)っ ♫ MUSIQUE AJOUTÉE ♫"
                        color = 0xC7CEEA
                    else:
                        title = "🎵 Ajouté à la file d'attente"
                        color = discord.Color.blue()
                        
                    embed = Embed(
                        title=title,
                        description=f"[{video['title']}]({video['webpage_url']})",
                        color=color
                    )
                    embed.set_thumbnail(url=video["thumbnail"])
                    if is_kawaii:
                        embed.set_footer(text="☆⌒(≧▽° )")
                    await interaction.followup.send(embed=embed)
            except Exception as e:
                print(f"Erreur conversion Spotify: {e}")
                continue
    else:
        # Vérifie si c'est un lien SoundCloud ou YouTube
        soundcloud_regex = re.compile(r'^(https?://)?(www\.)?(soundcloud\.com)/.+$')
        youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
        is_soundcloud = soundcloud_regex.match(query)
        is_youtube = youtube_regex.match(query)
        
        if is_soundcloud or is_youtube:
            try:
                ydl_opts = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": "in_playlist",
                }
                info = await extract_info_async(ydl_opts, query)
                
                if "entries" in info:
                    for entry in info["entries"]:
                        if entry:
                            await music_player.queue.put((entry["url"], True))

                    if info["entries"] and info["entries"][0]:
                        thumbnail = info["entries"][0].get("thumbnail")
                        if is_kawaii:
                            title = "✧･ﾟ: *✧･ﾟ:* PLAYLIST *:･ﾟ✧*:･ﾟ✧"
                            description = f"**{len(info['entries'])} musiques** ajoutées !"
                            color = 0xE2F0CB
                        else:
                            title = "🎶 Playlist ajoutée"
                            description = f"**{len(info['entries'])} titres** ont été ajoutés à la file d'attente."
                            color = discord.Color.green()
                            
                        embed = Embed(title=title, description=description, color=color)
                        if thumbnail:
                            embed.set_thumbnail(url=thumbnail)
                        await interaction.followup.send(embed=embed)
                else:
                    await music_player.queue.put((info["url"], False))
                    if is_kawaii:
                        title = "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ MUSIQUE AJOUTÉE"
                        color = 0xFFDAC1
                    else:
                        title = "🎵 Ajouté à la file d'attente"
                        color = discord.Color.blue()
                        
                    embed = Embed(
                        title=title,
                        description=f"[{info['title']}]({info['webpage_url']})",
                        color=color
                    )
                    if info.get("thumbnail"):
                        embed.set_thumbnail(url=info["thumbnail"])
                    await interaction.followup.send(embed=embed)
            except Exception as e:
                if is_kawaii:
                    description = "(´；ω；`) Problème avec cette vidéo..."
                    color = 0xFF9AA2
                else:
                    description = "Erreur lors de l'ajout de la vidéo ou de la playlist."
                    color = discord.Color.red()
                    
                embed = Embed(description=description, color=color)
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
                info = await extract_info_async(ydl_opts, query)
                video = info["entries"][0] if "entries" in info else info
                await music_player.queue.put((video["url"], False))
                
                if is_kawaii:
                    title = "ヽ(>∀<☆)ノ MUSIQUE TROUVÉE !"
                    color = 0xB5EAD7
                else:
                    title = "🎵 Ajouté à la file d'attente"
                    color = discord.Color.blue()
                    
                embed = Embed(
                    title=title,
                    description=f"[{video['title']}]({video['webpage_url']})",
                    color=color
                )
                if video.get("thumbnail"):
                    embed.set_thumbnail(url=video["thumbnail"])
                await interaction.followup.send(embed=embed)
            except Exception as e:
                if is_kawaii:
                    description = "(︶︹︺) Je n'ai pas trouvé cette musique..."
                    color = 0xFF9AA2
                else:
                    description = "Erreur lors de la recherche. Réessaie avec un autre titre."
                    color = discord.Color.red()
                    
                embed = Embed(description=description, color=color)
                await interaction.followup.send(embed=embed, ephemeral=True)
                print(f"Erreur : {e}")

    if not music_player.current_task or music_player.current_task.done():
        music_player.current_task = asyncio.create_task(play_audio(guild_id))

async def play_audio(guild_id):
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
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
            info = await extract_info_async(ydl_opts, url)
            audio_url = info['url']

            if is_playlist and music_player.text_channel:
                if is_kawaii:
                    title = "♫♬ MAINTENANT EN LECTURE ♬♫"
                    description = f"♪(´▽｀) [{info.get('title', 'Titre inconnu')}]({info.get('webpage_url', url)})"
                    color = 0xC7CEEA
                else:
                    title = "🎵 En cours de lecture"
                    description = f"[{info.get('title', 'Titre inconnu')}]({info.get('webpage_url', url)})"
                    color = discord.Color.green()
                    
                embed = Embed(title=title, description=description, color=color)
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

@bot.tree.command(name="pause", description="Met en pause la lecture en cours")
async def pause(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.pause()
        if is_kawaii:
            description = "(´･_･`) Musique en pause..."
            color = 0xFFB7B2
        else:
            description = "⏸️ Lecture mise en pause."
            color = discord.Color.orange()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed)
    else:
        if is_kawaii:
            description = "(・_・;) Rien ne joue actuellement..."
            color = 0xFF9AA2
        else:
            description = "Aucune lecture en cours."
            color = discord.Color.red()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="resume", description="Reprend la lecture")
async def resume(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.voice_client and music_player.voice_client.is_paused():
        music_player.voice_client.resume()
        if is_kawaii:
            description = "☆*:.｡.o(≧▽≦)o.｡.:*☆ C'est reparti !"
            color = 0xB5EAD7
        else:
            description = "▶️ Lecture reprise."
            color = discord.Color.green()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed)
    else:
        if is_kawaii:
            description = "(´･ω･`) Aucune musique en pause..."
            color = 0xFF9AA2
        else:
            description = "Aucune lecture mise en pause."
            color = discord.Color.red()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="skip", description="Passe à la chanson suivante")
async def skip(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.stop()
        if is_kawaii:
            description = "(ノ°ο°)ノ Skippé ! Prochaine musique ~"
            color = 0xE2F0CB
        else:
            description = "⏭️ Chanson actuelle ignorée."
            color = discord.Color.blue()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed)
    else:
        if is_kawaii:
            description = "(；一_一) Rien à skipper..."
            color = 0xFF9AA2
        else:
            description = "Aucune chanson en cours."
            color = discord.Color.red()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="loop", description="Active/désactive la boucle")
async def loop(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)
    
    music_player.loop_current = not music_player.loop_current
    
    if is_kawaii:
        state = "activée (◕‿◕✿)" if music_player.loop_current else "désactivée (︶︹︺)"
        color = 0xC7CEEA
    else:
        state = "activée" if music_player.loop_current else "désactivée"
        color = discord.Color.blue()
        
    embed = Embed(
        description=f"🔁 Lecture en boucle pour la musique actuelle {state}.",
        color=color
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stop", description="Arrête la lecture et déconnecte le bot")
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

        if is_kawaii:
            description = "(ﾉ´･ω･)ﾉ ﾐ ┸━┸ J'ai tout arrêté ! Bye bye ~"
            color = 0xFF9AA2
        else:
            description = "⏹️ Lecture arrêtée et bot déconnecté."
            color = discord.Color.red()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed)
    else:
        if is_kawaii:
            description = "(￣ω￣;) Je ne suis pas connecté..."
            color = 0xFF9AA2
        else:
            description = "Le bot n'est pas connecté à un salon vocal."
            color = discord.Color.red()
            
        embed = Embed(description=description, color=color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f"{bot.user.name} est en ligne.")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")

        async def rotate_presence():
            while True:
                if not bot.is_ready() or bot.is_closed():
                    return
                
                statuses = [
                    "vos liens Spotify 🎧",
                    "/play [lien] 🔥",
                ]
                
                for status in statuses:
                    try:
                        await bot.change_presence(
                            activity=discord.Activity(
                                name=status,
                                type=discord.ActivityType.listening
                            )
                        )
                        await asyncio.sleep(10)
                    except Exception as e:
                        print(f"Erreur changement statut: {e}")
                        await asyncio.sleep(5)

        bot.loop.create_task(rotate_presence())
        
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")
                
bot.run("TOKEN")
