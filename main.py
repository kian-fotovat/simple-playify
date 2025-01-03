import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp

# Intents pour le bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# Crée le bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Stockage des informations de lecture
class MusicPlayer:
    def __init__(self):
        self.voice_client = None
        self.current_task = None
        self.queue = asyncio.Queue()
        self.current_url = None  # URL actuellement jouée

music_player = MusicPlayer()

# Commande /play
@bot.tree.command(name="play", description="Joue un lien audio en streaming.")
@app_commands.describe(url="Lien YouTube ou SoundCloud à jouer")
async def play(interaction: discord.Interaction, url: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("Tu dois être dans un salon vocal pour utiliser cette commande.", ephemeral=True)
        return
    
    # Joindre le canal vocal si pas déjà connecté
    if not music_player.voice_client or not music_player.voice_client.is_connected():
        try:
            music_player.voice_client = await interaction.user.voice.channel.connect()
        except Exception as e:
            await interaction.response.send_message("Erreur lors de la connexion au canal vocal.", ephemeral=True)
            print(f"Erreur : {e}")
            return
    
    # Ajoute l'URL à la file d'attente
    await music_player.queue.put(url)
    await interaction.response.send_message(f"Lien ajouté à la file d'attente : {url}")

    # Si aucune tâche de lecture n'est en cours, démarre-en une
    if not music_player.current_task or music_player.current_task.done():
        music_player.current_task = asyncio.create_task(play_audio())

# Fonction pour lire l'audio
async def play_audio():
    while True:
        # Si la file d'attente est vide, arrêter la tâche
        if music_player.queue.empty():
            music_player.current_task = None
            break

        # Prendre le prochain lien de la file d'attente
        url = await music_player.queue.get()
        try:
            # Stocke l'URL actuelle
            music_player.current_url = url

            # Extraction du flux audio avec yt-dlp
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "default_search": "ytsearch",
                "source_address": "0.0.0.0",  # Corrige certains problèmes de réseau
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Si c'est une playlist, ajouter toutes les pistes à la file d'attente
                if "entries" in info:
                    for entry in info["entries"]:
                        await music_player.queue.put(entry["url"])
                    continue

                # Sinon, joue simplement le lien unique
                audio_url = info["url"]

            # Lecture en streaming
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn",
            }
            music_player.voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: print(f"Erreur : {e}") if e else None)

            # Attendre la fin de la lecture
            while music_player.voice_client.is_playing() or music_player.voice_client.is_paused():
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Erreur lors de la lecture de l'audio : {e}")

        # Si la file est vide, arrêter la tâche
        if music_player.queue.empty():
            music_player.current_task = None
            break

# Commande /pause
@bot.tree.command(name="pause", description="Met en pause la lecture en cours.")
async def pause(interaction: discord.Interaction):
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.pause()
        await interaction.response.send_message("Lecture mise en pause.")
    else:
        await interaction.response.send_message("Aucune lecture en cours.", ephemeral=True)

# Commande /resume
@bot.tree.command(name="resume", description="Reprend la lecture mise en pause.")
async def resume(interaction: discord.Interaction):
    if music_player.voice_client and music_player.voice_client.is_paused():
        music_player.voice_client.resume()
        await interaction.response.send_message("Lecture reprise.")
    else:
        await interaction.response.send_message("Aucune lecture mise en pause.", ephemeral=True)

# Commande /skip
@bot.tree.command(name="skip", description="Passe à la chanson suivante.")
async def skip(interaction: discord.Interaction):
    if music_player.voice_client and music_player.voice_client.is_playing():
        music_player.voice_client.stop()
        await interaction.response.send_message("Chanson actuelle ignorée.")
    else:
        await interaction.response.send_message("Aucune chanson en cours.", ephemeral=True)

# Commande /replay
@bot.tree.command(name="replay", description="Recommence la musique actuellement jouée.")
async def replay(interaction: discord.Interaction):
    if music_player.current_url:
        # Arrête la lecture actuelle (si en cours)
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        # Relance la musique en cours
        await music_player.queue.put(music_player.current_url)
        await interaction.response.send_message("Relecture de la musique actuelle.")
        
        # Si aucune tâche de lecture n'est en cours, démarre-en une
        if not music_player.current_task:
            music_player.current_task = asyncio.create_task(play_audio())
    else:
        await interaction.response.send_message("Aucune musique jouée précédemment.", ephemeral=True)

# Commande /stop
@bot.tree.command(name="stop", description="Arrête la lecture et déconnecte le bot.")
async def stop(interaction: discord.Interaction):
    if music_player.voice_client:
        await music_player.voice_client.disconnect()
        music_player.voice_client = None
        music_player.current_task = None
        music_player.current_url = None
        await interaction.response.send_message("Lecture arrêtée et bot déconnecté.")
    else:
        await interaction.response.send_message("Le bot n'est pas connecté à un salon vocal.", ephemeral=True)

# Lancer le bot
@bot.event
async def on_ready():
    print(f"{bot.user.name} est en ligne.")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes : {e}")

# Remplace par ton token
bot.run("TON_TOKEN")
