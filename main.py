import discord
from discord.ext import commands
from discord import app_commands, Embed
import asyncio
import yt_dlp
import re  # Pour détecter si le texte est un lien

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
        self.text_channel = None  # Canal texte pour envoyer les embeds

music_player = MusicPlayer()

# Commande /play améliorée
@bot.tree.command(name="play", description="Joue un lien ou recherche un titre sur YouTube.")
@app_commands.describe(query="Lien ou titre de la vidéo à jouer")
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        embed = Embed(
            description="Tu dois être dans un salon vocal pour utiliser cette commande.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Joindre le salon vocal si pas déjà connecté
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

    # Stocker le canal texte pour envoyer les embeds
    music_player.text_channel = interaction.channel

    # Vérifie si la requête est un lien
    url_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|soundcloud\.com)/.+$')
    is_url = url_regex.match(query)

    # Si c'est un lien, traite la playlist ou la vidéo
    if is_url:
        await interaction.response.defer()
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": "in_playlist",  # Pour récupérer toutes les vidéos de la playlist
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if "entries" in info:  # Si c'est une playlist
                    for entry in info["entries"]:
                        await music_player.queue.put((entry["url"], True))  # True = playlist

                    # Vérifier si la miniature est disponible
                    thumbnail = info["entries"][0].get("thumbnail") if info["entries"] else None

                    if thumbnail:
                        embed = Embed(
                            title="🎶 Playlist ajoutée",
                            description=f"**{len(info['entries'])} titres** ont été ajoutés à la file d'attente.",
                            color=discord.Color.green()
                        )
                        embed.set_thumbnail(url=thumbnail)  # Miniature de la première vidéo
                    else:
                        embed = Embed(
                            title="🎶 Playlist ajoutée",
                            description=f"**{len(info['entries'])} titres** ont été ajoutés à la file d'attente.",
                            color=discord.Color.green()
                        )
                    await interaction.followup.send(embed=embed)
                else:  # Si c'est une seule vidéo
                    await music_player.queue.put((info["url"], False))  # False = vidéo individuelle
                    embed = Embed(
                        title="🎵 Ajouté à la file d'attente",
                        description=f"[{info['title']}]({info['webpage_url']})",  # Utiliser l'URL publique
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=info["thumbnail"])  # Miniature de la vidéo
                    await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = Embed(
                description="Erreur lors de l'ajout de la vidéo ou de la playlist.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"Erreur : {e}")
    else:
        # Si ce n'est pas un lien, recherche sur YouTube
        await interaction.response.defer()  # Montre "bot réfléchit..." pour éviter les délais
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "default_search": "ytsearch1",  # Recherche uniquement le meilleur résultat
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                video_url = info["entries"][0]["url"]  # Premier résultat
                video_title = info["entries"][0]["title"]  # Titre du résultat
                video_thumbnail = info["entries"][0]["thumbnail"]  # Miniature du résultat
                video_webpage_url = info["entries"][0]["webpage_url"]  # URL publique
                await music_player.queue.put((video_url, False))  # False = vidéo individuelle
                embed = Embed(
                    title="🎵 Ajouté à la file d'attente",
                    description=f"[{video_title}]({video_webpage_url})",  # Utiliser l'URL publique
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=video_thumbnail)  # Miniature de la vidéo
                await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = Embed(
                description="Erreur lors de la recherche sur YouTube. Réessaie avec un autre titre.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"Erreur : {e}")

    # Démarre une tâche de lecture si aucune n'est en cours
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
            music_player.current_url = url
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "source_address": "0.0.0.0",  # Corrige certains problèmes de réseau
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Récupérer les informations de la vidéo
                video_title = info.get("title", "Titre inconnu")
                video_thumbnail = info.get("thumbnail", "https://via.placeholder.com/150")  # Miniature par défaut
                video_webpage_url = info.get("webpage_url", url)  # URL publique
                audio_url = info.get("url")  # URL audio

                # Si l'URL audio n'est pas trouvée, essayer une autre méthode
                if not audio_url:
                    formats = info.get("formats", [])
                    for f in formats:
                        if f.get("acodec") != "none":  # Format avec audio
                            audio_url = f.get("url")
                            break

                if not audio_url:
                    raise Exception("Impossible de trouver une URL audio valide.")

                # Envoyer un embed "En cours de lecture" uniquement pour les playlists
                if is_playlist and music_player.text_channel:
                    embed = Embed(
                        title="🎵 En cours de lecture",
                        description=f"[{video_title}]({video_webpage_url})",  # Utiliser l'URL publique
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(url=video_thumbnail)
                    await music_player.text_channel.send(embed=embed)

                # Lire l'audio
                ffmpeg_options = {
                    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    "options": "-vn",
                }
                music_player.voice_client.play(
                    discord.FFmpegPCMAudio(audio_url, **ffmpeg_options),
                    after=lambda e: print(f"Erreur : {e}") if e else None
                )

                # Attendre la fin de la lecture
                while music_player.voice_client.is_playing() or music_player.voice_client.is_paused():
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"Erreur lors de la lecture de l'audio : {e}")
            # Passer à la musique suivante en cas d'erreur
            continue

        if music_player.queue.empty():
            music_player.current_task = None
            break

# Commande /pause
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

# Commande /resume
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

# Commande /skip
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

# Commande /replay
@bot.tree.command(name="replay", description="Recommence la musique actuellement jouée.")
async def replay(interaction: discord.Interaction):
    if music_player.current_url:
        if music_player.voice_client and music_player.voice_client.is_playing():
            music_player.voice_client.stop()

        await music_player.queue.put((music_player.current_url, False))  # False = vidéo individuelle
        embed = Embed(
            description="🔁 Relecture de la musique actuelle.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

        if not music_player.current_task:
            music_player.current_task = asyncio.create_task(play_audio())
    else:
        embed = Embed(
            description="Aucune musique jouée précédemment.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /stop
@bot.tree.command(name="stop", description="Arrête la lecture et déconnecte le bot.")
async def stop(interaction: discord.Interaction):
    if music_player.voice_client:
        # Arrêter la lecture en cours et annuler la tâche active
        if music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        # Vide la file d'attente
        while not music_player.queue.empty():
            music_player.queue.get_nowait()

        # Déconnecte le bot
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
