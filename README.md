[🇬🇧 English version](https://github.com/alan7383/playify/blob/main/README_EN.md)

<h1 align="center">

🎵 Playify - Le bot musical ultime  

---

<p align="center">
  <img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="image" width="900">
</p>

## 🚀 Pourquoi choisir Playify ?  

> **📢 Grande nouvelle !** Après **plus de deux mois de travail**, **Spotify est enfin pris en charge** dans Playify ! 🎉  
> 👉 **Encore en bêta** : les **titres Spotify fonctionnent parfaitement**, et les **playlists fonctionnent si elles sont courtes**.  
> Le support complet des playlists arrive très bientôt !  

🧡 Si vous appréciez le travail derrière cette nouvelle fonctionnalité, **un petit don serait grandement apprécié** ☕ 👉 [Faire un don](https://www.paypal.com/paypalme/alanmussot1)

- **🎶 Musique fluide** : Lecture depuis YouTube, SoundCloud **et maintenant Spotify** !
- **📝 Commandes simples** : Play, pause, skip, stop, replay... et plus encore !
- **🐄 Playlists personnalisées** : Créez, gérez et écoutez vos musiques préférées.
- **🔊 Qualité audio premium** : Profitez d'un son optimisé sans compromis.
- **⚡️ Architecture boostée** : Propulsé par **yt-dlp**, **FFmpeg**, et un système de file d’attente asynchrone ultra-réactif.  

---

## 🏡 Héberger Playify chez vous  

### ⚙️ Prérequis  

- **Python 3.9+** ➞ [Télécharger ici](https://www.python.org/downloads/)  
- **FFmpeg** ➞ [Installer ici](https://ffmpeg.org/download.html)  
- **Un token Discord** ➞ [Obtenir un token](https://discord.com/developers/applications)  
- **Un compte développeur Spotify** ➞ [Créer une application ici](https://developer.spotify.com/dashboard/applications)  
- **Dépendances** ➞ Installées via `requirements.txt`  

### 🧩 Configuration Spotify  

> Pour activer Spotify, vous devez créer une application sur le portail Spotify Developers :

1. Allez sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)  
2. Créez une nouvelle application  
3. Récupérez les identifiants suivants :  
   - `Client ID`  
   - `Client Secret`  
4. Dans `main.py`, remplacez les lignes suivantes par vos identifiants personnels :

```python
# Configuration Spotify
SPOTIFY_CLIENT_ID = 'votre_client_id'
SPOTIFY_CLIENT_SECRET = 'votre_client_secret'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))
````

💡 *Ne partagez jamais ces identifiants publiquement !*

### 📌 Installation

```bash
git clone https://github.com/alan7383/playify.git
cd playify
pip install -r requirements.txt
```

Ajoutez votre token Discord dans un fichier `.env` :

```env
DISCORD_TOKEN=Votre_Token_Discord
```

### 🎮 Lancer le bot

```bash
python main.py
```

*Sur Linux/Mac : `python3 main.py`*

Si vous êtes allergique à la ligne de commande, double-cliquez simplement sur `lancer_bot.bat`.

---

## 🔗 Pas envie de l’héberger ?

Pas de stress ! Playify est déjà en ligne 24/7. Ajoutez-le à votre serveur ici :
➡ **[Inviter Playify](https://discord.com/oauth2/authorize?client_id=1330613913569726575&permissions=8&integration_type=0&scope=bot)**

---

## 💡 Contribuer

Les contributions sont **les bienvenues** !

1. **Forkez** ce repo
2. **Créez** une branche
3. **Proposez** une pull request

Vous avez une idée ou un bug à signaler ? Ouvrez une **issue** !

---

## ☕ Soutenir le projet

Si Playify vous plaît – surtout maintenant avec Spotify 🎧 – et que vous voulez m’envoyer un petit café pour continuer à développer tout ça :
👉 **[Faire un don sur PayPal](https://www.paypal.com/paypalme/alanmussot1)**

---

## 📝 Licence

Ce projet est sous licence **MIT**. Faites-en bon usage ! 🔥
