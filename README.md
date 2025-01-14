<h1 align="center">

Playify 🎵

---

<img src="![github-banner-modified](https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360)" alt="image" width="900">

</h1>

## Fonctionnalités

- Lecture de musique depuis YouTube et SoundCloud
- Commandes intuitives (play, pause, skip, stop, replay, etc.)
- Gestion des playlists
- Latence minimale pour une écoute fluide
- Qualité d'écoute maximale

---

## Héberger Playify chez vous

Voici les étapes pour héberger Playify sur votre propre machine :

### Prérequis

1. **Python 3.9 ou plus** doit être installé.
2. **FFmpeg** doit être installé et configuré dans votre PATH.
3. Un token Discord pour votre bot (que vous pouvez obtenir depuis le [Discord Developer Portal](https://discord.com/developers/applications)).
4. Installez les bibliothèques nécessaires à l'aide de `requirements.txt`.

### Installation

1. Clonez ce repository :
   ```bash
   git clone https://github.com/alan7383/playify.git
   cd playify
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Créez un fichier `.env` pour stocker votre token Discord **(facultatif)** :
   ```env
   DISCORD_TOKEN=Votre_Token_Discord
   ```

5. Lancer le bot :
   ```bash
   python main.py
   ```

### Notes supplémentaires

- Assurez-vous que le bot a les permissions nécessaires pour rejoindre des salons vocaux et envoyer des messages.
- Si vous avez des problèmes, vérifiez les logs affichés dans la console.

---

## Pas envie d’héberger Playify vous-même ?

Pas de souci ! Vous pouvez inviter Playify directement dans vos serveurs. Il est hébergé 24/7 par moi-même. (@alananasss sur Discord)

Cliquez ici pour l’ajouter : [Lien d'invitation](https://discord.com/oauth2/authorize?client_id=1323070239222665267&permissions=8&integration_type=0&scope=bot)

---

## Contribuer

Les contributions sont les bienvenues ! Si vous souhaitez ajouter des fonctionnalités ou corriger des bugs :

1. Forkez le repository
2. Créez une branche pour vos modifications
3. Proposez une pull request

---

## Licence

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser, de le modifier et de le redistribuer.

