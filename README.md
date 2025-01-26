<h1 align="center">

Playify 🎵

---

<img src="https://github.com/user-attachments/assets/5c1d5fba-3a34-4ffe-bd46-ef68e1175360" alt="image" width="900">

## Fonctionnalités

- Lecture de musique depuis YouTube et SoundCloud
- Commandes intuitives (play, pause, skip, stop, replay, etc.)
- Gestion des playlists : Créez, gérez et lisez vos playlists favorites
- Latence minimale pour une écoute fluide grâce à une architecture optimisée
- Qualité d'écoute maximale, avec un rendu audio de haute qualité

---

## Héberger Playify chez vous

Voici les étapes pour héberger Playify sur votre propre machine :

### Prérequis

1. **Python 3.9 ou plus** doit être installé. Vous pouvez télécharger Python ici : [python.org](https://www.python.org/downloads/).
2. **FFmpeg** doit être installé et configuré dans votre PATH. Vous pouvez suivre cette [documentation](https://ffmpeg.org/download.html) pour l'installation.
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

3. Créez un fichier `.env` pour stocker votre token Discord **(facultatif mais recommandé)** :
   ```env
   DISCORD_TOKEN=Votre_Token_Discord
   ```
   *Ne partagez jamais votre token Discord publiquement.*

4. **Option supplémentaire** : Si vous préférez ne pas utiliser la ligne de commande, vous pouvez simplement double-cliquer sur le fichier `lancer_bot.bat` pour lancer le bot directement.

5. Lancer le bot :
   ```bash
   python main.py
   ```
   *Si vous utilisez un système Unix (Linux/Mac), utilisez `python3 main.py`.*

### Notes supplémentaires

- Assurez-vous que le bot a les permissions nécessaires pour rejoindre des salons vocaux et envoyer des messages.
- Si vous avez des problèmes, vérifiez les logs affichés dans la console pour plus d'informations.

---

## Pas envie d’héberger Playify vous-même ?

Pas de souci ! Vous pouvez inviter Playify directement dans vos serveurs. Il est hébergé 24/7 par moi-même. (@alananasssss sur Discord)

Cliquez ici pour l’ajouter : [Lien d'invitation](https://discord.com/oauth2/authorize?client_id=1330613913569726575&permissions=8&integration_type=0&scope=bot)

---

## Contribuer

Les contributions sont les bienvenues ! Si vous souhaitez ajouter des fonctionnalités ou corriger des bugs :

1. Forkez le repository
2. Créez une branche pour vos modifications
3. Proposez une pull request

### Soumettre des issues

Si vous rencontrez des problèmes ou avez des suggestions de nouvelles fonctionnalités, veuillez vérifier d'abord les issues existantes ou créer une nouvelle issue.

### Soutenir le projet

Si vous appréciez le projet et souhaitez me soutenir financièrement, vous pouvez faire un don via PayPal ici : [Soutenir sur PayPal](https://www.paypal.com/paypalme/alanmussot1)

---

## Licence

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser, de le modifier et de le redistribuer. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
