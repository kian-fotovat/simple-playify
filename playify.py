# ==============================================================================
# 1. IMPORTS & GLOBAL CONFIGURATION
# ==============================================================================

# --- Imports ---

import discord
from discord.ext import commands
from discord import app_commands, Embed
from discord.ui import View, Button
from discord import ButtonStyle
from discord.app_commands import Choice
import asyncio
import yt_dlp
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotify_scraper import SpotifyClient
from spotify_scraper.core.exceptions import SpotifyScraperError
import random
from urllib.parse import urlparse, parse_qs
from cachetools import TTLCache
import logging
import requests
from playwright.async_api import async_playwright
import json
import time
import syncedlyrics
import lyricsgenius
import psutil
import time
import datetime
import platform
import sys
import math # Needed for the format_bytes helper
import traceback # --- NEW --- To format exceptions
import os
import shutil
from dotenv import load_dotenv
load_dotenv()

SILENT_MESSAGES = True

# --- Logging ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- API Tokens & Clients ---

GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")

if GENIUS_TOKEN and GENIUS_TOKEN != "YOUR_GENIUS_TOKEN_HERE":
    genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False, remove_section_headers=True)
    logger.info("LyricsGenius client initialized.")
else:
    genius = None
    logger.warning("GENIUS_TOKEN is not set in the code. /lyrics and fallback will not work.")

# Official API Client (fast and prioritized)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))
    logger.info("Spotipy API Client successfully initialized.")
except Exception as e:
    sp = None
    logger.error(f"Could not initialize Spotipy client: {e}")

# Scraper Client (backup plan, without Selenium)
try:
    # Using "requests" mode, more reliable on a server
    spotify_scraper_client = SpotifyClient(browser_type="requests")
    logger.info("SpotifyScraper client successfully initialized in requests mode.")
except Exception as e:
    spotify_scraper_client = None
    logger.error(f"Could not initialize SpotifyScraper: {e}")

# --- Caching ---

url_cache = TTLCache(maxsize=75000, ttl=7200)

# --- Bot Configuration Dictionaries ---

# Dictionary of available audio filters and their FFmpeg options
AUDIO_FILTERS = {
    "slowed": "asetrate=44100*0.8",
    "spedup": "asetrate=44100*1.2",
    "nightcore": "asetrate=44100*1.25,atempo=1.0",
    "reverb": "aecho=0.8:0.9:40|50|60:0.4|0.3|0.2",
    "8d": "apulsator=hz=0.08",
    "muffled": "lowpass=f=500",
    "bassboost": "bass=g=10", # Boost bass by 10 dB
    "earrape": "acrusher=level_in=8:level_out=18:bits=8:mode=log:aa=1" # Ear rape effect
}

# Dictionary to map filter values to their display names
FILTER_DISPLAY_NAMES = {
    "none": "None",
    "slowed": "Slowed ♪",
    "spedup": "Sped Up ♫",
    "nightcore": "Nightcore ☆",
    "reverb": "Reverb",
    "8d": "8D Audio",
    "muffled": "Muffled",
    "bassboost": "Bass Boost",
    "earrape": "Earrape"
}

messages = {
    # --- NEW --- Error reporting messages
    "critical_error_title": {
        "normal": "🚨 An Unexpected Error Occurred",
        "kawaii": "(╥﹏╥) Oh no! A critical error happened..."
    },
    "critical_error_description": {
        "normal": "The bot encountered a problem. Please report this issue on GitHub so we can fix it!",
        "kawaii": "Something went wrong... (´；ω；`) Can you please tell the developers on GitHub so they can make me better?"
    },
    "critical_error_report_field": {
        "normal": "Report on GitHub",
        "kawaii": "Report the boo-boo! 🩹"
    },
    "critical_error_report_value": {
        "normal": "You can create an issue here:\n**https://github.com/alan7383/playify/issues**\n\nPlease include the error details below.",
        "kawaii": "Please tell them what happened here:\n**https://github.com/alan7383/playify/issues**\n\nDon't forget to send the little error message below!~"
    },
    "critical_error_details_field": {
        "normal": "Error Details",
        "kawaii": "Error info (for the smart people!)"
    },
    # ... (rest of your messages dictionary)
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
    "spotify_error_title": {
        "normal": "🚨 Spotify Error",
        "kawaii": "(´；ω；`) Spotify Error!"
    },
    "spotify_error_description_detailed": {
        "normal": "Could not process this Spotify link.\n\n**Probable reason:** The playlist might be private, deleted, or unavailable in the bot's region.\n\n*The fallback method also failed, which can happen if Spotify recently updated its website.*",
        "kawaii": "(´；ω；`) Oh no! I couldn't get the songs from this Spotify link...\n\n**Maybe...** it's a secret playlist, or it ran away! My backup magic didn't work either; Spotify might have changed its clothes, and I don't recognize it anymore..."
    },
    "spotify_playlist_added": {
        "normal": "🎶 Spotify Playlist Added",
        "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ SPOTIFY PLAYLIST"
    },
    "spotify_playlist_description": {
        "normal": "**{count} tracks** added, {failed} failed.\n{failed_tracks}",
        "kawaii": "**{count} songs** added, {failed} couldn’t join! (´･ω･`)\n{failed_tracks}"
    },
    "deezer_error": {
        "normal": "Error processing the Deezer link. It may be private, region-locked, or invalid.",
        "kawaii": "(´；ω；`) Oh no! Problem with the Deezer link... maybe it’s shy or hidden?"
    },
    "deezer_playlist_added": {
        "normal": "🎶 Deezer Playlist Added",
        "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ DEEZER PLAYLIST"
    },
    "deezer_playlist_description": {
        "normal": "**{count} tracks** added, {failed} failed.\n{failed_tracks}",
        "kawaii": "**{count} songs** added, {failed} couldn’t join! (´･ω･`)\n{failed_tracks}"
    },
    "apple_music_error": {
        "normal": "Error processing the Apple Music link.",
        "kawaii": "(´；ω；`) Oops! Trouble with the Apple Music link..."
    },
    "apple_music_playlist_added": {
        "normal": "🎶 Apple Music Playlist Added",
        "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ APPLE MUSIC PLAYLIST"
    },
    "apple_music_playlist_description": {
        "normal": "**{count} tracks** added, {failed} failed.\n{failed_tracks}",
        "kawaii": "**{count} songs** added, {failed} couldn't join! (´･ω･`)\n{failed_tracks}"
    },
    "tidal_error": {
        "normal": "Error processing the Tidal link. It may be private, region-locked, or invalid.",
        "kawaii": "(´；ω；`) Oh no! Problem with the Tidal link... maybe it’s shy or hidden?"
    },
    "tidal_playlist_added": {
        "normal": "🎶 Tidal Playlist Added",
        "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ TIDAL PLAYLIST"
    },
    "tidal_playlist_description": {
        "normal": "**{count} tracks** added, {failed} failed.\n{failed_tracks}",
        "kawaii": "**{count} songs** added, {failed} couldn’t join! (´･ω･`)\n{failed_tracks}"
    },
    "amazon_music_error": {
        "normal": "Error processing the Amazon Music link.",
        "kawaii": "(´；ω；`) Oh no! Something is wrong with the Amazon Music link..."
    },
    "amazon_music_playlist_added": {
        "normal": "🎶 Amazon Music Playlist Added",
        "kawaii": "☆*:.｡.o(≧▽≦)o.｡.:*☆ AMAZON MUSIC PLAYLIST"
    },
    "amazon_music_playlist_description": {
        "normal": "**{count} tracks** added, {failed} failed.\n{failed_tracks}",
        "kawaii": "**{count} songs** added, {failed} couldn't join! (´･ω･`)\n{failed_tracks}"
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
        "kawaii": "disabled (¨_°`)"
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
    "filter_title": {
        "normal": "🎧 Audio Filters",
        "kawaii": "🎧 Filters! ヾ(≧▽≦*)o"
    },
    "filter_description": {
        "normal": "Click on the buttons to enable or disable a filter in real time!",
        "kawaii": "Clicky clicky to change the sound! ~☆"
    },
    "no_filter_playback": {
        "normal": "Nothing is currently playing to apply a filter on.",
        "kawaii": "Nothing is playing... (´・ω・`)"
    },
    "lyrics_fallback_warning": {
        "normal": "Synced lyrics not found. Displaying standard lyrics instead.",
        "kawaii": "I couldn't find the synced lyrics... (｡•́︿•̀｡) But here are the normal ones for u!"
    },
    "karaoke_disclaimer": {
        "normal": "Please note: The timing of the arrow (») and lyric accuracy are matched automatically and can vary based on the song version or active filters.",
        "kawaii": "Just so you know! ପ(๑•ᴗ•๑)ଓ ♡ The arrow (») and lyrics do their best to sync up! But with different song versions or fun filters, they might not be perfectly on time~"
    },
    "karaoke_warning_title": {
        "normal": "🎤 Karaoke - Important Notice",
        "kawaii": "🎤 Karaoke Time! Just a little note~ (´• ω •`)"
    },
    "karaoke_warning_description": {
        "normal": "Please note that the timing of the lyrics (») is matched automatically and can vary.\n\n**💡 Pro Tip:** For the best results, try adding `topic` or `audio` to your search (e.g., `party addict kets4eki topic`).\n\nPress **Continue** to start.",
        "kawaii": "The timing of the lyrics (») does its best to be perfect, but sometimes it's a little shy! ପ(๑•ᴗ•๑)ଓ ♡\n\n**💡 Pro Tip:** For the bestest results, try adding `topic` or `audio` to your search, like `party addict kets4eki topic`!\n\nSmash that **Continue** button to begin~ 💖"
    },
    "karaoke_warning_button": {
        "normal": "Continue",
        "kawaii": "Continue (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
    },
    "lyrics_not_found_title": {
        "normal": "😢 Lyrics Not Found",
        "kawaii": "૮( ´• ˕ •` )ა Lyrics not found..."
    },
    "lyrics_not_found_description": {
        "normal": "I couldn't find lyrics for **{query}**.\n\nYou can refine the search yourself. Try using just the song title.",
        "kawaii": "I searched everywhere but I couldn't find the lyrics for **{query}** (｡•́︿•̀｡)\n\nTry searching just with the title, you can do it!~"
    },
    "lyrics_refine_button": {
        "normal": "Refine Search",
        "kawaii": "Try again! (o･ω･)ﾉ"
    },
    "karaoke_not_found_title": {
        "normal": "😢 Synced Lyrics Not Found",
        "kawaii": "૮( ´• ˕ •` )ა Synced Lyrics Not Found..."
    },
    "karaoke_not_found_description": {
        "normal": "I couldn't find synced lyrics for **{query}**.\n\nYou can refine the search or search for standard (non-synced) lyrics on Genius.",
        "kawaii": "I looked everywhere but couldn't find the synced lyrics for **{query}** (｡•́︿•̀｡)\n\nYou can try again, or we can look for the normal lyrics on Genius together!~"
    },
    "karaoke_retry_button": {
        "normal": "Refine Search",
        "kawaii": "Try Again! (o･ω･)ﾉ"
    },
    "karaoke_genius_fallback_button": {
        "normal": "Search on Genius",
        "kawaii": "Find on Genius 📜"
    },
    "karaoke_retry_success": {
        "normal": "Lyrics found! Starting karaoke...",
        "kawaii": "Yay, I found them! Starting karaoke~ 🎤"
    },
    "karaoke_retry_fail": {
        "normal": "Sorry, I still couldn't find synced lyrics for **{query}**.",
        "kawaii": "Aww, still no luck finding the synced lyrics for **{query}**... (´-ω-`)"
    },
        "extraction_error": {
        "normal": "⚠️ Could Not Add Track",
        "kawaii": "(ﾉ><)ﾉ I couldn't add that one!"
    },
    "extraction_error_reason": {
        "normal": "Reason: {error_message}",
        "kawaii": "Here's why: {error_message} (´• ω •`)"
    },
        "error_title_age_restricted": {
        "normal": "Age-Restricted Video",
        "kawaii": "Video for Grown-ups! (⁄ ⁄>⁄ ᗨ ⁄<⁄ ⁄)"
    },
    "error_desc_age_restricted": {
        "normal": "This video requires sign-in to confirm the user's age and cannot be played by the bot.",
        "kawaii": "This video is for big kids only! I'm not old enough to watch it... (>_<)"
    },
    "error_title_private": {
        "normal": "Private Video",
        "kawaii": "Secret Video! (・-・)"
    },
    "error_desc_private": {
        "normal": "This video is marked as private and cannot be accessed.",
        "kawaii": "This video is a super secret! I'm not on the guest list... ( T_T)"
    },
    "error_title_unavailable": {
        "normal": "Video Unavailable",
        "kawaii": "Video went poof! (o.o)"
    },
    "error_desc_unavailable": {
        "normal": "This video is no longer available or may have been removed.",
        "kawaii": "Poof! This video has disappeared... I can't find it anywhere!"
    },
    "error_title_generic": {
        "normal": "Access Denied",
        "kawaii": "Access Denied! (壁)"
    },
    "error_desc_generic": {
        "normal": "The bot was blocked from accessing this video. This can happen with certain live streams or premieres.",
        "kawaii": "A big wall is blocking me from this video! I can't get through..."
    },
    "error_field_full_error": {
        "normal": "Full Error for Bug Report",
        "kawaii": "The techy stuff for the devs!"
    },
        "error_field_what_to_do": {
        "normal": "What to do?",
        "kawaii": "What can we do? (・_・?)"
    },
    "error_what_to_do_content": {
        "normal": "Some videos have restrictions that prevent bots from playing them.\n\nIf you believe this is a different bug, please [open an issue on GitHub]({github_link}).",
        "kawaii": "Some videos have super strong shields that stop me! ( >д<)\n\nIf you think something is really, really broken, you can [tell the super smart developers here]({github_link})!~"
    },
    "discord_command_title": {
        "normal": "🔗 Join Our Discord!",
        "kawaii": "Come hang out with us!"
    },
    "discord_command_description": {
        "normal": "Click the button below to join the official Playify support and community server.",
        "kawaii": "Join our super cute community! Just click the button below~ (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
    },
    "discord_command_button": {
        "normal": "Join Server",
        "kawaii": "Join Us! ♡"
    },
    "24_7_on_title": {
        "normal": "📻 24/7 Radio ON",
        "kawaii": "📻 24/7 Radio ON ✧"
    },
    "24_7_on_desc": {
        "normal": "Queue will loop indefinitely – bot stays & auto-resumes when you re-join.",
        "kawaii": "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Radio forever! Bot never sleeps, just pauses when alone~"
    },
    "24_7_off_title": {
        "normal": "📴 24/7 Radio OFF",
        "kawaii": "📴 24/7 Radio OFF (；一_一)"
    },
    "24_7_off_desc": {
        "normal": "Queue cleared – bot will disconnect after 60 s if left alone.",
        "kawaii": "Bye-bye radio! Queue wiped, bot will nap soon~"
    },
        "24_7_auto_title": {
        "normal": "🔄 24/7 Auto Mode",
        "kawaii": "🔄 24/7 Auto Mode ✨"
    },
    "24_7_auto_desc": {
        "normal": "Autoplay enabled - will add similar songs when playlist ends!",
        "kawaii": "Autoplay on! New similar songs will appear magically~ ✨"
    },
    "24_7_normal_title": {
        "normal": "🔁 24/7 Loop Mode",
        "kawaii": "🔁 24/7 Loop Mode ♾️"
    },
    "24_7_normal_desc": {
        "normal": "Playlist will loop indefinitely without adding new songs.",
        "kawaii": "Playlist looping forever~ No new songs added! ♾️"
    },
    "24_7_invalid_mode": {
        "normal": "Invalid mode! Use `/24_7 auto` or `/24_7 normal`",
        "kawaii": "Oops! Use `/24_7 auto` or `/24_7 normal` (◕‿◕)"
    },
        # --- NEW --- Messages for the instant /queue
    "queue_page_footer": {
        "normal": "Page {current_page}/{total_pages}",
        "kawaii": "Page {current_page}/{total_pages}  (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
    },
    "previous_button": {
        "normal": "⬅️ Previous",
        "kawaii": "⬅️ Back"
    },
    "next_button": {
        "normal": "Next ➡️",
        "kawaii": "Next! ➡️"
    },
    "queue_status_title": {
        "normal": "Current Status",
        "kawaii": "Status! (o･ω･)ﾉ"
    },
    "queue_status_none": {
        "normal": "No special modes active.",
        "kawaii": "Just chillin' normally~"
    },
    "queue_status_loop": {
        "normal": "🔁 **Loop (Song)**: Enabled",
        "kawaii": "🔁 **Loop (Song)**: On! 💖"
    },
    "queue_status_24_7": {
        "normal": "📻 **24/7 ({mode})**: Enabled",
        "kawaii": "📻 **24/7 ({mode})**: Let's go! ✨"
    },
    "queue_status_autoplay": {
        "normal": "➡️ **Autoplay**: Enabled",
        "kawaii": "➡️ **Autoplay**: On! ♫"
    },
    "now_playing_in_queue": {
        "normal": "▶️ Now Playing",
        "kawaii": "▶️ Now Playing!~"
    },
    "reconnect_start": {
        "normal": "🔃 Reconnecting to the voice channel to improve stability...",
        "kawaii": "🔃 Reconnecting to make things smooooth~ (o･ω･)ﾉ"
    },
    "reconnect_success": {
        "normal": "✅ Reconnected! Resuming playback from where you left off.",
        "kawaii": "✅ Reconnected! Let's continue the party~ ヽ(o^ ^o)ﾉ"
    },
    "reconnect_not_playing": {
        "normal": "I can only reconnect during active playback.",
        "kawaii": "I can only do my magic reconnect trick when a song is playing! (´• ω •`)"
    },
    "autoplay_direct_link_notice": {
        "normal": "💿 The last track was a direct link, which can't be used for recommendations. Searching queue history for a compatible song to start Autoplay...",
        "kawaii": "💿 The last song was a direct link! I can't find similar songs for that one... (´• ω •`) Looking through our playlist for another song to use!~"
    },
    "autoplay_file_notice": {
        "normal": "💿 The last track was a local file, which can't be used for recommendations. Searching queue history for a compatible song to start Autoplay...",
        "kawaii": "💿 The last song was a file! I can't find similar songs for that one... (´• ω •`) Looking through our playlist for another song to use!~"
    },
    # --- NEW --- Messages for /skip with kaomoji
    "skip_confirmation": {
        "normal": "⏭️ Song Skipped!",
        "kawaii": "⏭️ Skipped!~ (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
    },
    "skip_queue_empty": {
        "normal": "The queue is now empty.",
        "kawaii": "The queue is empty now... (´･ω･`)"
    },
    # --- NEW --- Messages for /remove with kaomoji
    "remove_title": {
        "normal": "🗑️ Remove Songs",
        "kawaii": "🗑️ Remove Songs! (o･ω･)ﾉ"
    },
    "remove_description": {
        "normal": "Use the dropdown menu to select one or more songs to remove.\nUse the buttons to navigate if you have more than 25 songs.",
        "kawaii": "Pick the songs to say bye-bye to!~ ☆\nUse the buttons if you have lots and lots of songs!"
    },
    "remove_placeholder": {
        "normal": "Select one or more songs to remove...",
        "kawaii": "Which songs should go?~ ♡"
    },
    "remove_success_title": {
        "normal": "✅ {count} Song(s) Removed",
        "kawaii": "✅ Poof! {count} song(s) are gone!~"
    },
    "remove_processed": {
        "normal": "*Selection has been processed.*",
        "kawaii": "*All done!~ (´• ω •`)*"
    },
    "replay_success_title": {
        "normal": "🎵 Song Replayed",
        "kawaii": "🎵 Playing it again!~"
    },
    "replay_success_desc": {
        "normal": "Restarting [{title}]({url}) from the beginning.",
        "kawaii": "Let's listen to [{title}]({url}) one more time!~ (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
    },
}

# --- Discord Bot Initialization ---

# Intents for the bot
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

# Create the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================================================================
# 2. CORE CLASSES & STATE MANAGEMENT
# ==============================================================================

# --- Global State Variables ---

# Server states
music_players = {}  # {guild_id: MusicPlayer()}
kawaii_mode = {}    # {guild_id: bool}
server_filters = {} # {guild_id: set("filter1", "filter2")}
karaoke_disclaimer_shown = set()
_24_7_active = {}  # {guild_id: bool}

# --- Core Music Player Class ---

class MusicPlayer:
    def __init__(self):
        self.voice_client = None
        self.current_task = None
        self.queue = asyncio.Queue()
        self.history = []
        self.radio_playlist = [] 
        self.current_url = None
        self.current_info = None
        self.text_channel = None
        self.loop_current = False
        self.autoplay_enabled = False
        self.last_was_single = False
        self.start_time = 0
        self.playback_started_at = None
        self.active_filter = None
        self.seek_info = None

        # --- Attributes for lyrics, karaoke, and filters ---
        self.lyrics_task = None
        self.lyrics_message = None
        self.synced_lyrics = None
        self.is_seeking = False
        self.playback_speed = 1.0
        
        self.is_reconnecting = False 
        self.is_current_live = False

        self.hydration_task = None
        self.hydration_lock = asyncio.Lock()
        
        # --- ADD THIS LINE ---
        self.suppress_next_now_playing = False

        self.is_auto_promoting = False
        self.is_cleaning = False
        self.is_resuming_after_clean = False
        self.resume_info = None
        self.is_resuming_live = False
        self.silence_task = None 
        self.is_playing_silence = False

# --- Discord UI Classes (Views & Modals) ---

class LyricsView(View):
    def __init__(self, pages: list, original_embed: Embed):
        super().__init__(timeout=300.0)
        self.pages = pages
        self.original_embed = original_embed
        self.current_page = 0

    def update_embed(self):
        self.original_embed.description = self.pages[self.current_page]
        self.original_embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")
        return self.original_embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey, row=0)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1

        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = False

        await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey, row=0)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1

        self.next_button.disabled = self.current_page == len(self.pages) - 1
        self.previous_button.disabled = False

        await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @discord.ui.button(label="Refine", emoji="✏️", style=discord.ButtonStyle.secondary, row=0)
    async def refine_button(self, interaction: discord.Interaction, button: Button):
        modal = RefineLyricsModal(message_to_edit=interaction.message)
        await interaction.response.send_modal(modal)

class LyricsRetryModal(discord.ui.Modal, title="Refine Lyrics Search"):
    def __init__(self, original_interaction: discord.Interaction, suggested_query: str):
        super().__init__()
        self.original_interaction = original_interaction
        self.suggested_query = suggested_query
        self.guild_id = original_interaction.guild_id

        self.corrected_query = discord.ui.TextInput(
            label="Song Title & Artist",
            placeholder="e.g., Believer Imagine Dragons",
            default=self.suggested_query,
            style=discord.TextStyle.short
        )
        self.add_item(self.corrected_query)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        new_query = self.corrected_query.value
        logger.info(f"Retrying lyrics search with new query: '{new_query}'")

        try:
            loop = asyncio.get_running_loop()
            if not genius:
                await interaction.followup.send("Genius API is not configured.", silent=SILENT_MESSAGES, ephemeral=True)
                return

            song = await loop.run_in_executor(None, lambda: genius.search_song(new_query))

            if not song:
                fail_message = get_messages("lyrics_not_found_description", self.guild_id).format(query=new_query)
                await interaction.followup.send(fail_message.split('\n')[0], silent=SILENT_MESSAGES, ephemeral=True)
                return

            raw_lyrics = song.lyrics
            lines = raw_lyrics.split('\n')
            cleaned_lines = [line for line in lines if "contributor" not in line.lower() and "lyrics" not in line.lower() and "embed" not in line.lower()]
            lyrics = "\n".join(cleaned_lines).strip()

            pages = []
            current_page_content = ""
            for line in lyrics.split('\n'):
                if len(current_page_content) + len(line) + 1 > 1500:
                    pages.append(f"```{current_page_content.strip()}```")
                    current_page_content = ""
                current_page_content += line + "\n"
            if current_page_content.strip():
                pages.append(f"```{current_page_content.strip()}```")

            base_embed = Embed(title=f"📜 Lyrics for {song.title}", url=song.url, color=discord.Color.green())

            view = LyricsView(pages=pages, original_embed=base_embed)
            initial_embed = view.update_embed()

            view.children[0].disabled = True
            if len(pages) <= 1:
                view.children[1].disabled = True

            message = await self.original_interaction.followup.send(silent=SILENT_MESSAGES,embed=initial_embed, view=view, wait=True)

            view.message = message

            await interaction.followup.send("Lyrics found!", silent=SILENT_MESSAGES, ephemeral=True)

        except Exception as e:
            logger.error(f"Error during lyrics retry: {e}")
            await interaction.followup.send("An error occurred during the new search.", silent=SILENT_MESSAGES, ephemeral=True)

class LyricsRetryView(discord.ui.View):
    # We add guild_id to the initialization
    def __init__(self, original_interaction: discord.Interaction, suggested_query: str, guild_id: int):
        super().__init__(timeout=180.0)
        self.original_interaction = original_interaction
        self.suggested_query = suggested_query

        # We get the correct label for the button
        button_label = get_messages("lyrics_refine_button", guild_id)

        # We access the button (created by the decorator) and change its label
        self.retry_button.label = button_label

    # The decorator no longer needs the label; it is defined dynamically
    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def retry_button(self, interaction: discord.Interaction, button: Button):
        modal = LyricsRetryModal(
            original_interaction=self.original_interaction,
            suggested_query=self.suggested_query
        )
        await interaction.response.send_modal(modal)

class KaraokeRetryModal(discord.ui.Modal, title="Refine Karaoke Search"):
    def __init__(self, original_interaction: discord.Interaction, suggested_query: str):
        super().__init__()
        self.original_interaction = original_interaction
        self.suggested_query = suggested_query
        self.guild_id = original_interaction.guild_id
        self.music_player = get_player(self.guild_id)
        self.is_kawaii = get_mode(self.guild_id)

        self.corrected_query = discord.ui.TextInput(
            label="Song Title & Artist",
            placeholder="e.g., Believer Imagine Dragons",
            default=self.suggested_query,
            style=discord.TextStyle.short
        )
        self.add_item(self.corrected_query)

    # THIS IS THE METHOD THAT WAS MISSING
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        new_query = self.corrected_query.value
        logger.info(f"Retrying synced lyrics search with new query: '{new_query}'")

        loop = asyncio.get_running_loop()
        lrc = None
        try:
            lrc = await asyncio.wait_for(
                loop.run_in_executor(None, syncedlyrics.search, new_query),
                timeout=10.0
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.error(f"Error during karaoke retry search: {e}")

        if not lrc:
            fail_message = get_messages("karaoke_retry_fail", self.guild_id).format(query=new_query)
            await interaction.followup.send(fail_message, silent=SILENT_MESSAGES, ephemeral=True)
            return

        lyrics_lines = [{'time': int(m.group(1))*60000 + int(m.group(2))*1000 + int(m.group(3)), 'text': m.group(4).strip()} for line in lrc.splitlines() if (m := re.match(r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)', line))]

        if not lyrics_lines:
            fail_message = get_messages("karaoke_retry_fail", self.guild_id).format(query=new_query)
            await interaction.followup.send(fail_message, silent=SILENT_MESSAGES, ephemeral=True)
            return

        # Success! Start the karaoke.
        self.music_player.synced_lyrics = lyrics_lines

        clean_title, _ = get_cleaned_song_info(self.music_player.current_info)
        embed = Embed(
            title=f"🎤 Karaoke for {clean_title}",
            description="Starting karaoke...",
            color=0xC7CEEA if self.is_kawaii else discord.Color.blue()
        )

        # We use the original interaction's followup to send the main message
        lyrics_message = await self.original_interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, wait=True)
        self.music_player.lyrics_message = lyrics_message
        self.music_player.lyrics_task = asyncio.create_task(update_karaoke_task(self.guild_id))

        # Notify the user who clicked the button that it worked
        success_message = get_messages("karaoke_retry_success", self.guild_id)
        await interaction.followup.send(success_message, silent=SILENT_MESSAGES, ephemeral=True)

class RefineLyricsModal(discord.ui.Modal, title="Refine Lyrics Search"):
    def __init__(self, message_to_edit: discord.Message):
        super().__init__()
        self.message_to_edit = message_to_edit
        self.guild_id = message_to_edit.guild.id
        self.is_kawaii = get_mode(self.guild_id)

        self.corrected_query = discord.ui.TextInput(
            label="New Song Title & Artist",
            placeholder="e.g., Blinding Lights The Weeknd",
            style=discord.TextStyle.short
        )
        self.add_item(self.corrected_query)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        new_query = self.corrected_query.value
        logger.info(f"Refining lyrics search with new query: '{new_query}'")

        if not genius:
            await interaction.followup.send("Genius API is not configured.", silent=SILENT_MESSAGES, ephemeral=True)
            return

        try:
            loop = asyncio.get_running_loop()
            song = await loop.run_in_executor(None, lambda: genius.search_song(new_query))

            if not song:
                await interaction.followup.send(f"Sorry, I still couldn't find lyrics for **{new_query}**.", silent=SILENT_MESSAGES, ephemeral=True)
                return

            raw_lyrics = song.lyrics
            lines = raw_lyrics.split('\n')
            cleaned_lines = [line for line in lines if "contributor" not in line.lower() and "lyrics" not in line.lower() and "embed" not in line.lower()]
            lyrics = "\n".join(cleaned_lines).strip()

            pages = []
            current_page_content = ""
            for line in lyrics.split('\n'):
                if len(current_page_content) + len(line) + 1 > 1500:
                    pages.append(f"```{current_page_content.strip()}```")
                    current_page_content = ""
                current_page_content += line + "\n"
            if current_page_content.strip():
                pages.append(f"```{current_page_content.strip()}```")

            new_embed = Embed(
                title=f"📜 Lyrics for {song.title}",
                url=song.url,
                color=0xB5EAD7 if self.is_kawaii else discord.Color.green()
            )

            new_view = LyricsView(pages=pages, original_embed=new_embed)

            final_embed = new_view.update_embed()
            new_view.children[0].disabled = True
            if len(pages) <= 1:
                new_view.children[1].disabled = True

            await self.message_to_edit.edit(embed=final_embed, view=new_view)


            await interaction.followup.send("Lyrics updated successfully!", silent=SILENT_MESSAGES, ephemeral=True)

        except Exception as e:
            logger.error(f"Error during lyrics refinement: {e}", exc_info=True)
            await interaction.followup.send("An error occurred during the new search.", silent=SILENT_MESSAGES, ephemeral=True)

class KaraokeRetryView(discord.ui.View):
    def __init__(self, original_interaction: discord.Interaction, suggested_query: str, guild_id: int):
        super().__init__(timeout=180.0)
        self.original_interaction = original_interaction
        self.suggested_query = suggested_query
        self.guild_id = guild_id

        # Set button labels from messages
        self.retry_button.label = get_messages("karaoke_retry_button", self.guild_id)
        self.genius_fallback_button.label = get_messages("karaoke_genius_fallback_button", self.guild_id)

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def retry_button(self, interaction: discord.Interaction, button: Button):
        modal = KaraokeRetryModal(
            original_interaction=self.original_interaction,
            suggested_query=self.suggested_query
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def genius_fallback_button(self, interaction: discord.Interaction, button: Button):
        # Disable buttons to show action is taken
        for child in self.children:
            child.disabled = True
        await self.original_interaction.edit_original_response(view=self)

        # Acknowledge the button click before starting the search
        await interaction.response.defer()

        # Fetch standard lyrics
        fallback_msg = get_messages("lyrics_fallback_warning", self.guild_id)
        await fetch_and_display_genius_lyrics(self.original_interaction, fallback_message=fallback_msg)

class KaraokeWarningView(View):
    def __init__(self, interaction: discord.Interaction, karaoke_coro):
        super().__init__(timeout=180.0)
        self.interaction = interaction
        self.karaoke_coro = karaoke_coro # The coroutine to execute after the click

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        # We check that it's the original user who is clicking
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("Only the person who ran the command can do this!", silent=SILENT_MESSAGES, ephemeral=True)
            return

        # We add the server to the list of "warned" guilds
        guild_id = interaction.guild_id
        karaoke_disclaimer_shown.add(guild_id)
        logger.info(f"Karaoke disclaimer acknowledged for guild {guild_id}.")

        # We disable the button and update the message
        button.disabled = True
        button.label = "Acknowledged!"
        await interaction.response.edit_message(view=self)

        # We start the actual karaoke logic
        await self.karaoke_coro()

# View for the filter buttons
class FilterView(View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.guild_id = interaction.guild.id
        self.interaction = interaction
        server_filters.setdefault(self.guild_id, set())
        for effect, display_name in FILTER_DISPLAY_NAMES.items():
            is_active = effect in server_filters[self.guild_id]
            style = ButtonStyle.success if is_active else ButtonStyle.secondary
            button = Button(label=display_name, custom_id=f"filter_{effect}", style=style)
            button.callback = self.button_callback
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        effect = interaction.data['custom_id'].split('_')[1]
        active_guild_filters = server_filters[self.guild_id]

        # Enable or disable the filter
        if effect in active_guild_filters:
            active_guild_filters.remove(effect)
        else:
            active_guild_filters.add(effect)

        # Update the appearance of the buttons
        for child in self.children:
            if isinstance(child, Button):
                child_effect = child.custom_id.split('_')[1]
                child.style = ButtonStyle.success if child_effect in active_guild_filters else ButtonStyle.secondary

        await interaction.response.edit_message(view=self)

        music_player = get_player(self.guild_id)
        if music_player.voice_client and (music_player.voice_client.is_playing() or music_player.voice_client.is_paused()):

            # --- START OF CORRECTION ---

            # 1. We save the CURRENT playback speed (before the change)
            old_speed = music_player.playback_speed

            # 2. We calculate the real time elapsed since playback started
            elapsed_time = 0
            if music_player.playback_started_at:
                real_elapsed_time = time.time() - music_player.playback_started_at
                # 3. We calculate the position IN the music using the OLD speed
                elapsed_time = (real_elapsed_time * old_speed) + music_player.start_time

            # 4. We update the player's speed with the NEW speed for the next playback
            music_player.playback_speed = get_speed_multiplier_from_filters(active_guild_filters)

            # --- END OF CORRECTION ---

            # We indicate that we are changing the filter to restart playback at the correct position
            music_player.is_seeking = True
            music_player.seek_info = elapsed_time
            music_player.voice_client.stop()

# --- NEW --- View for the paginated /queue command

class QueueView(View):
    """
    A View that handles pagination for the /queue command.
    It's designed to be fast and intelligently fetches missing titles on-the-fly.
    """
    def __init__(self, interaction: discord.Interaction, tracks: list, items_per_page: int = 5):
        super().__init__(timeout=300.0)
        self.interaction = interaction
        self.guild_id = interaction.guild_id
        self.music_player = get_player(self.guild_id)
        self.is_kawaii = get_mode(self.guild_id)

        self.tracks = tracks
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = math.ceil(len(self.tracks) / self.items_per_page) if self.tracks else 1

        self.previous_button = Button(label=get_messages("previous_button", self.guild_id), style=ButtonStyle.secondary)
        self.next_button = Button(label=get_messages("next_button", self.guild_id), style=ButtonStyle.secondary)

        self.previous_button.callback = self.previous_button_callback
        self.next_button.callback = self.next_button_callback
        
        self.add_item(self.previous_button)
        self.add_item(self.next_button)

    async def create_queue_embed(self) -> Embed:
        status_lines = []
        if self.music_player.loop_current:
            status_lines.append(get_messages("queue_status_loop", self.guild_id))
        if _24_7_active.get(self.guild_id, False):
            mode_24_7 = "Auto" if self.music_player.autoplay_enabled else "Normal"
            status_lines.append(get_messages("queue_status_24_7", self.guild_id).format(mode=mode_24_7))
        elif self.music_player.autoplay_enabled:
            status_lines.append(get_messages("queue_status_autoplay", self.guild_id))
        status_description = "\n".join(status_lines) if status_lines else get_messages("queue_status_none", self.guild_id)

        embed = Embed(
            title=get_messages("queue_title", self.guild_id),
            description=get_messages("queue_description", self.guild_id).format(count=len(self.tracks)),
            color=0xB5EAD7 if self.is_kawaii else discord.Color.blue()
        )
        embed.add_field(name=get_messages("queue_status_title", self.guild_id), value=status_description, inline=False)
        
        if self.music_player.current_info:
            title = self.music_player.current_info.get("title", "Unknown Title")
            now_playing_text = ""
            if self.music_player.current_info.get('source_type') == 'file':
                now_playing_text = f"💿 `{title}`"
            else:
                url = self.music_player.current_info.get("webpage_url", self.music_player.current_url)
                now_playing_text = f"[{title}]({url})"
            embed.add_field(name=get_messages("now_playing_in_queue", self.guild_id), value=now_playing_text, inline=False)

        if self.tracks:
            start_index = self.current_page * self.items_per_page
            end_index = start_index + self.items_per_page
            tracks_on_page = self.tracks[start_index:end_index]

            tracks_to_hydrate = [track for track in tracks_on_page if (not track.get('title') or track.get('title') == 'Unknown Title') and not track.get('source_type') == 'file']
            
            if tracks_to_hydrate:
                tasks = [fetch_meta(track['url'], extract_info_async) for track in tracks_to_hydrate]
                hydrated_results = await asyncio.gather(*tasks)
                hydrated_map = {res['url']: res for res in hydrated_results if res}
                for track in tracks_on_page:
                    if track['url'] in hydrated_map:
                        new_data = hydrated_map[track['url']]
                        track['title'] = new_data.get('title', 'Unknown Title')
                        track['webpage_url'] = new_data.get('webpage_url', track['url'])

            next_songs_list = []
            current_length = 0
            limit = 1000
            
            for i, item in enumerate(tracks_on_page, start=start_index):
                title = item.get('title', 'Title not available')
                display_line = ""
                if item.get('source_type') == 'file':
                    display_line = f"💿 `{title}`"
                else:
                    url = item.get('webpage_url', '#')
                    display_line = f"[{title}]({url})"
                
                full_line = f"`{i + 1}.` {display_line}\n"

                if current_length + len(full_line) > limit:
                    remaining = len(self.tracks) - (i)
                    next_songs_list.append(f"\n... and {remaining} more song(s).")
                    break
                
                next_songs_list.append(full_line)
                current_length += len(full_line)
            
            if next_songs_list:
                embed.add_field(name=get_messages("queue_next", self.guild_id), value="".join(next_songs_list), inline=False)

        embed.set_footer(text=get_messages("queue_page_footer", self.guild_id).format(current_page=self.current_page + 1, total_pages=self.total_pages))
        return embed
    
    def update_button_states(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1

    async def previous_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.current_page > 0:
            self.current_page -= 1
        self.update_button_states()
        new_embed = await self.create_queue_embed()
        
        try:
            await interaction.edit_original_response(embed=new_embed, view=self)
        except discord.errors.DiscordServerError as e:
            logger.warning(f"Failed to edit queue message (previous button) due to Discord API error: {e}")

    async def next_button_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        self.update_button_states()
        new_embed = await self.create_queue_embed()
        
        try:
            await interaction.edit_original_response(embed=new_embed, view=self)
        except discord.errors.DiscordServerError as e:
            logger.warning(f"Failed to edit queue message (next button) due to Discord API error: {e}")

class RemoveSelect(discord.ui.Select):
    """ The dropdown menu component, now with multi-select enabled. """
    def __init__(self, tracks_on_page: list, page_offset: int, guild_id: int):
        options = []
        for i, track in enumerate(tracks_on_page):
            global_index = i + page_offset
            options.append(discord.SelectOption(
                label=f"{global_index + 1}. {track.get('title', 'Unknown Title')}"[:100],
                value=str(global_index)
            ))
        
        super().__init__(
            placeholder=get_messages("remove_placeholder", guild_id),
            min_values=1,
            max_values=len(options) if options else 1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """ This is the corrected callback that properly handles the interaction response. """
        guild_id = interaction.guild_id
        is_kawaii = get_mode(guild_id)
        music_player = get_player(guild_id)
        
        indices_to_remove = sorted([int(v) for v in self.values], reverse=True)
        
        queue_list = list(music_player.queue._queue)
        removed_titles = []

        for index in indices_to_remove:
            if 0 <= index < len(queue_list):
                removed_track = queue_list.pop(index)
                removed_titles.append(removed_track.get('title', 'a song'))
            
        new_queue = asyncio.Queue()
        for item in queue_list:
            await new_queue.put(item)
        music_player.queue = new_queue

        self.view.clear_items()
        await interaction.response.edit_message(content=get_messages("remove_processed", guild_id), embed=None, view=self.view)

        embed = Embed(
            title=get_messages("remove_success_title", guild_id).format(count=len(removed_titles)),
            description="\n".join([f"• `{title}`" for title in removed_titles]),
            color=0xB5EAD7 if is_kawaii else discord.Color.green()
        )
        await interaction.channel.send(embed=embed, silent=SILENT_MESSAGES)

class RemoveView(View):
    """ The interactive view holding the dropdown and pagination buttons. """
    def __init__(self, interaction: discord.Interaction, all_tracks: list):
        super().__init__(timeout=300.0)
        self.interaction = interaction
        self.guild_id = interaction.guild_id
        self.all_tracks = all_tracks
        self.current_page = 0
        self.items_per_page = 25
        self.total_pages = math.ceil(len(self.all_tracks) / self.items_per_page) if self.all_tracks else 1
        
    async def update_view(self):
        """ Asynchronously hydrates tracks for the current page and rebuilds components. """
        self.clear_items()

        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page
        tracks_on_page = self.all_tracks[start_index:end_index]

        tracks_to_hydrate = [t for t in tracks_on_page if (not t.get('title') or t.get('title') == 'Unknown Title') and not t.get('source_type') == 'file']
        
        if tracks_to_hydrate:
            logger.info(f"RemoveView: Hydrating {len(tracks_to_hydrate)} tracks for page {self.current_page + 1}")
            tasks = [fetch_meta(track['url'], extract_info_async) for track in tracks_to_hydrate]
            hydrated_results = await asyncio.gather(*tasks)
            hydrated_map = {res['url']: res for res in hydrated_results if res}
            for track in tracks_on_page:
                if track['url'] in hydrated_map:
                    track['title'] = hydrated_map[track['url']].get('title', 'Unknown Title')

        self.add_item(RemoveSelect(tracks_on_page, page_offset=start_index, guild_id=self.guild_id))

        if self.total_pages > 1:
            prev_button = Button(label="⬅️ Previous", style=ButtonStyle.secondary, disabled=(self.current_page == 0))
            next_button = Button(label="Next ➡️", style=ButtonStyle.secondary, disabled=(self.current_page >= self.total_pages - 1))
            
            prev_button.callback = self.prev_page
            next_button.callback = self.next_page
            
            self.add_item(prev_button)
            self.add_item(next_button)
            
    async def prev_page(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_view()
        await interaction.edit_original_response(view=self)

    async def next_page(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        await self.update_view()
        await interaction.edit_original_response(view=self)

# ==============================================================================
# 3. UTILITY & HELPER FUNCTIONS
# ==============================================================================

# --- General & State Helpers ---

async def play_silence_loop(guild_id: int):
    """
    Plays a silent looping sound generated by FFmpeg to keep the voice connection active.
    This version is fixed to stop properly.
    """
    music_player = get_player(guild_id)
    vc = music_player.voice_client

    if not vc or not vc.is_connected():
        return

    logger.info(f"[{guild_id}] Starting FFmpeg silence loop to keep connection alive.")
    music_player.is_playing_silence = True
    
    source = 'anullsrc=channel_layout=stereo:sample_rate=48000'
    FFMPEG_OPTS = {'before_options': '-f lavfi', 'options': '-vn -c:a libopus -b:a 16k'}

    try:
        while vc.is_connected():
            if not vc.is_playing():
                vc.play(discord.FFmpegPCMAudio(source, **FFMPEG_OPTS))
            await asyncio.sleep(20)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"[{guild_id}] Error in FFmpeg silence loop: {e}")
    finally:
        if vc.is_connected() and vc.is_playing() and music_player.is_playing_silence:
            logger.info(f"[{guild_id}] Cleanly stopping silence source.")
            vc.stop()
        music_player.is_playing_silence = False

async def ensure_voice_connection(interaction: discord.Interaction) -> discord.VoiceClient | None:
    """
    Verify and guarantee that the bot is connected to the user's vocal salon. 
    Change the connection, the reconnexion and the promotion on the screens. 
    This version includes a robust auto gear mechanism for “zombies” connections 
    If the speaker completes it, it comprises the file attachment and the progression of the file in the course. 
    Retour the client's vocals in the success box, None in the check box.
    """
    guild_id = interaction.guild.id
    music_player = get_player(guild_id)
    is_kawaii = get_mode(guild_id)

    member = interaction.guild.get_member(interaction.user.id)
    if not member or not member.voice or not member.voice.channel:
        embed = Embed(description=get_messages("no_voice_channel", guild_id), color=0xFF9AA2 if is_kawaii else discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        return None

    voice_channel = member.voice.channel
    vc = interaction.guild.voice_client

    if vc and not vc.is_connected():
        logger.warning(f"[{guild_id}] Outdated/disconnected voice client found. Cleanup.")
        music_player.voice_client = None
        vc = None
        
    if vc and music_player.voice_client != vc:
        logger.info(f"[{guild_id}] Voice client state desynchronization detected. Resynchronizing.")
        music_player.voice_client = vc

    if not vc:
        try:
            new_vc = await voice_channel.connect()
            music_player.voice_client = new_vc
            vc = new_vc 
            logger.info(f"[{guild_id}] Successfully connected to voice channel: {voice_channel.name}")

            if music_player.is_resuming_after_clean and music_player.resume_info:
                logger.info(f"[{guild_id}] Resume playback after clean reconnect.")
                url_to_resume = music_player.resume_info['url']
                time_to_resume = music_player.resume_info['time']
                info_to_resume = music_player.resume_info['info']
                music_player.current_url = url_to_resume
                music_player.current_info = info_to_resume
                bot.loop.create_task(play_audio(guild_id, seek_time=time_to_resume))
                music_player.is_resuming_after_clean = False
                music_player.resume_info = None

        except discord.errors.ClientException as e:
            logger.error(f"[{guild_id}] Caught ClientException: '{e}'. Forcing a logout and attempting to recover state.")
            guild_vc = interaction.guild.voice_client
            if guild_vc:
                try:
                    if guild_vc.is_playing() and music_player.current_info:
                        elapsed_time = time.time() - music_player.playback_started_at
                        current_timestamp = music_player.start_time + (elapsed_time * music_player.playback_speed)
                        music_player.resume_info = {
                            'url': music_player.current_url,
                            'time': current_timestamp,
                            'info': music_player.current_info.copy()
                        }
                        music_player.is_resuming_after_clean = True
                        logger.info(f"[{guild_id}] Resume state saved at {current_timestamp:.2f}s before cleanup.")

                    music_player.is_cleaning = True
                    await guild_vc.disconnect(force=True)
                    await asyncio.sleep(1) 
                finally:
                    music_player.is_cleaning = False

            return await ensure_voice_connection(interaction)

        except Exception as e:
            embed = Embed(description=get_messages("connection_error", guild_id), color=0xFF9AA2 if is_kawaii else discord.Color.red())
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
            logger.error(f"Connection error: {e}", exc_info=True)
            return None

    elif vc.channel != voice_channel:
        logger.info(f"[{guild_id}] Moving to a new voice channel: {voice_channel.name}")
        await vc.move_to(voice_channel)
        await asyncio.sleep(0.5)

    if isinstance(vc.channel, discord.StageChannel):
        if interaction.guild.me.voice and interaction.guild.me.voice.suppress:
            logger.info(f"[{guild_id}] The bot is as a spectator. Attempting to promote.")
            try:
                await interaction.guild.me.edit(suppress=False)
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                logger.warning(f"[{guild_id}] Promotion failed: 'Mute Members' permission missing.")
            except Exception as e:
                logger.error(f"[{guild_id}] Unexpected error while promoting: {e}")

    music_player.text_channel = interaction.channel
    music_player.voice_client = vc
    return vc

def clear_audio_cache(guild_id: int):
    """Deletes the audio cache directory for a specific guild."""
    guild_cache_path = os.path.join("audio_cache", str(guild_id))
    if os.path.exists(guild_cache_path):
        try:
            shutil.rmtree(guild_cache_path)
            logger.info(f"Audio cache for guild {guild_id} successfully cleared.")
        except Exception as e:
            logger.error(f"Error while deleting cache for guild {guild_id}: {e}")

# --- NEW --- Helper functions for instant /queue
def get_full_opts():
    """Returns standard options for fetching full metadata."""
    return {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 10,
    }

async def fetch_meta(url, extract_info_async):
    """Fetches metadata for a single URL, used for queue hydration."""
    try:
        data = await extract_info_async(get_full_opts(), url)
        # We return a dictionary in the same format as our queue items
        return {
            'url': url,
            'title': data.get('title', 'Unknown Title'),
            'webpage_url': data.get('webpage_url', url),
            'thumbnail': data.get('thumbnail'),
            'is_single': False # Assume it's part of a list
        }
    except Exception as e:
        logger.warning(f"Failed to hydrate metadata for {url}: {e}")
        return None # Return None on failure
    
# --- NEW --- Background task to fetch missing metadata without blocking
async def background_queue_hydrator(guild_id: int):
    """
    A background task that iterates through the queue and fetches metadata
    for items that only have a URL, without blocking the main thread.
    """
    music_player = get_player(guild_id)
    
    # Use a lock to ensure this task only runs once at a time
    async with music_player.hydration_lock:
        logger.info(f"[{guild_id}] Starting background queue hydration...")
        
        # Iterate over a copy of the queue
        queue_snapshot = list(music_player.queue._queue)
        
        for item in queue_snapshot:
            # If the title is missing or is the default placeholder, fetch it
            if not item.get('title') or item.get('title') == 'Unknown Title':
                try:
                    hydrated_data = await fetch_meta(item['url'], extract_info_async)
                    if hydrated_data:
                        # Update the original dictionary object in the queue directly
                        item['title'] = hydrated_data.get('title', 'Unknown Title')
                        item['webpage_url'] = hydrated_data.get('webpage_url', item['url'])
                        item['thumbnail'] = hydrated_data.get('thumbnail')
                        logger.debug(f"[{guild_id}] Hydrated: {item['title']}")
                except Exception as e:
                    logger.warning(f"[{guild_id}] Background hydration failed for {item['url']}: {e}")
                
                # IMPORTANT: Pause briefly between fetches to avoid blocking the event loop
                await asyncio.sleep(1.5)

    logger.info(f"[{guild_id}] Background queue hydration finished.")

# Get player for a server
def get_player(guild_id):
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer()
    return music_players[guild_id]

# Get active filter for a server
def get_filter(guild_id):
    return server_filters.get(guild_id)

# Get kawaii mode
def get_mode(guild_id):
    return kawaii_mode.get(guild_id, False)

def get_messages(message_key, guild_id):
    is_kawaii = get_mode(guild_id)
    mode = "kawaii" if is_kawaii else "normal"
    return messages[message_key][mode]

def create_queue_item_from_info(info: dict) -> dict:
    """
    Creates a standardized, clean queue item from a full yt-dlp info dict.
    This version correctly handles the difference between local files and online sources.
    """
    
    # --- NEW: Special handling for local files ---
    # If the source_type is 'file', we build a very specific and clean dictionary
    # to ensure no data from previous online songs can interfere.
    if info.get('source_type') == 'file':
        return {
            'url': info.get('url'),  # This is the essential file path
            'title': info.get('title', 'Unknown File'),
            'webpage_url': None,     # A local file has no webpage URL
            'thumbnail': None,       # A local file has no thumbnail
            'is_single': False,      # When re-queuing, it's considered part of a list
            'source_type': 'file'    # Critically preserve this type
        }

    # --- Original logic for all online sources (YouTube, SoundCloud, etc.) ---
    # This part remains the same as before.
    return {
        'url': info.get('webpage_url', info.get('url')), # Prioritize the user-friendly URL
        'title': info.get('title', 'Unknown Title'),
        'webpage_url': info.get('webpage_url', info.get('url')),
        'thumbnail': info.get('thumbnail'),
        'is_single': False, # When re-queuing, it's part of a loop, not a single add
        'source_type': info.get('source_type') # Preserve for other potential types
    }

# --- Text, Formatting & Lyrics Helpers ---

def get_cleaned_song_info(music_info: dict) -> tuple[str, str]:
    """Aggressively cleans the title and artist to optimize the search."""

    title = music_info.get("title", "Unknown Title")
    artist = music_info.get("uploader", "Unknown Artist")

    # --- 1. Cleaning the artist name ---
    # ADDING "- Topic" TO THE LIST
    ARTIST_NOISE = ['xoxo', 'official', 'beats', 'prod', 'music', 'records', 'tv', 'lyrics', 'archive', '- Topic']
    clean_artist = artist
    for noise in ARTIST_NOISE:
        clean_artist = re.sub(r'(?i)' + re.escape(noise), '', clean_artist).strip()

    # --- 2. Cleaning the song title ---
    patterns_to_remove = [
        r'\[.*?\]',              # Removes content in brackets, e.g., [MV]
        r'\(.*?\)',              # Removes content in parentheses, e.g., (Official Video)
        r'\s*feat\..*',          # Removes "feat." and the rest
        r'\s*ft\..*',            # Removes "ft." and the rest
        # --- LINE ADDED BELOW ---
        r'\s*w/.*',              # Removes "w/" (with) and the rest
        # --- END OF ADDITION ---
        r'(?i)official video',   # Removes "official video" (case-insensitive)
        r'(?i)lyric video',      # Removes "lyric video" (case-insensitive)
        r'(?i)audio',            # Removes "audio" (case-insensitive)
        r'(?i)hd',               # Removes "hd" (case-insensitive)
        r'4K',                   # Removes "4K"
        r'\+',                   # Removes "+" symbols
    ]

    clean_title = title
    for pattern in patterns_to_remove:
        clean_title = re.sub(pattern, '', clean_title)

    # Tries to remove the artist name from the title to keep only the song name
    if clean_artist:
        clean_title = clean_title.replace(clean_artist, '')
    clean_title = clean_title.replace(artist, '').strip(' -')

    # If the title is empty after cleaning, start over from the original title without parentheses/brackets
    if not clean_title:
        clean_title = re.sub(r'\[.*?\]|\(.*?\)', '', title).strip()

    logger.info(f"Cleaned info: Title='{clean_title}', Artist='{clean_artist}'")
    return clean_title, clean_artist

def get_speed_multiplier_from_filters(active_filters: set) -> float:
    """Calculates the speed multiplier from the active filters."""
    speed = 1.0
    pitch_speed = 1.0 # Speed from asetrate (nightcore/slowed)
    tempo_speed = 1.0 # Speed from atempo

    for f in active_filters:
        if f in AUDIO_FILTERS:
            filter_value = AUDIO_FILTERS[f]
            if "atempo=" in filter_value:
                match = re.search(r"atempo=([\d\.]+)", filter_value)
                if match:
                    tempo_speed *= float(match.group(1))
            if "asetrate=" in filter_value:
                match = re.search(r"asetrate=[\d\.]+\*([\d\.]+)", filter_value)
                if match:
                    pitch_speed *= float(match.group(1))

    # The final speed is the product of the two
    speed = pitch_speed * tempo_speed
    return speed

async def fetch_and_display_genius_lyrics(interaction: discord.Interaction, fallback_message: str = None):
    """Fetches, formats, and displays lyrics with smart pagination buttons."""
    guild_id = interaction.guild_id
    music_player = get_player(guild_id)
    is_kawaii = get_mode(guild_id)
    loop = asyncio.get_running_loop()

    if not genius:
        return await interaction.followup.send("Genius API is not configured.", silent=SILENT_MESSAGES, ephemeral=True)

    clean_title, artist_name = get_cleaned_song_info(music_player.current_info)
    precise_query = f"{clean_title} {artist_name}"

    try:
        # Attempt 1: Asynchronous precise search
        logger.info(f"Attempting precise Genius search: '{precise_query}'")
        song = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: genius.search_song(precise_query)),
            timeout=10.0
        )

        # Attempt 2: If the first one fails
        if not song:
            logger.info(f"Precise Genius search failed, trying broad search: '{clean_title}'")
            song = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: genius.search_song(clean_title)),
                timeout=10.0
            )

        if not song:
            # We retrieve the texts from the `messages` dictionary
            error_title = get_messages("lyrics_not_found_title", guild_id)
            error_desc = get_messages("lyrics_not_found_description", guild_id).format(query=precise_query)

            error_embed = Embed(
                title=error_title,
                description=error_desc,
                color=0xFF9AA2 if get_mode(guild_id) else discord.Color.red()
            )

            # We pass the guild_id to the view so it can choose the correct text for the button
            view = LyricsRetryView(
                original_interaction=interaction,
                suggested_query=clean_title,
                guild_id=guild_id
            )
            await interaction.followup.send(silent=SILENT_MESSAGES,embed=error_embed, view=view)
            return

        # --- The rest of the logic (fetching lyrics, pagination) ---
        raw_lyrics = song.lyrics
        lines = raw_lyrics.split('\n')

        cleaned_lines = []
        for line in lines:
            if "contributor" in line.lower() or "lyrics" in line.lower() or "embed" in line.lower():
                continue
            cleaned_lines.append(line)

        lyrics = "\n".join(cleaned_lines).strip()

        pages = []
        current_page_content = ""
        max_page_length = 1500

        for line in lyrics.split('\n'):
            if len(current_page_content) + len(line) + 1 > max_page_length:
                pages.append(f"```{current_page_content.strip()}```")
                current_page_content = ""
            current_page_content += line + "\n"

        if current_page_content.strip():
            pages.append(f"```{current_page_content.strip()}```")

        if not pages:
            return await interaction.followup.send("Could not format the lyrics.", silent=SILENT_MESSAGES, ephemeral=True)

        base_embed = Embed(
            title=f"📜 Lyrics for {song.title}",
            color=0xB5EAD7 if is_kawaii else discord.Color.green(),
            url=song.url
        )
        if fallback_message:
            base_embed.set_author(name=fallback_message)

        view = LyricsView(pages=pages, original_embed=base_embed)
        initial_embed = view.update_embed()

        view.children[0].disabled = True
        if len(pages) <= 1:
            view.children[1].disabled = True

        message = await interaction.followup.send(silent=SILENT_MESSAGES,embed=initial_embed, view=view, wait=True)

        view.message = message

    except asyncio.TimeoutError:
        logger.error(f"Genius search timed out for '{clean_title}'.")
        await interaction.followup.send("Sorry, the lyrics search took too long to respond. Please try again later.", silent=SILENT_MESSAGES, ephemeral=True)
    except Exception as e:
        logger.error(f"Error fetching/displaying Genius lyrics for '{clean_title}': {e}")
        await interaction.followup.send("An error occurred while displaying the lyrics.", silent=SILENT_MESSAGES, ephemeral=True)

def format_lyrics_display(lyrics_lines, current_line_index):
    """
    Formats the lyrics for Discord display, correctly handling
    newlines and problematic Markdown characters.
    """
    def clean(text):
        # Replaces backticks and removes Windows newlines (\r)
        return text.replace('`', "'").replace('\r', '')

    display_parts = []

    # Defines the context (how many lines to show before/after)
    context_lines = 4

    # Handles the case where the karaoke has not started yet
    if current_line_index == -1:
        display_parts.append("*(Waiting for the first line...)*\n")
        # We display the next 5 lines
        for line_obj in lyrics_lines[:5]:
            # We split each line in case it contains newlines
            for sub_line in clean(line_obj['text']).split('\n'):
                if sub_line.strip(): # Ignore empty lines
                    display_parts.append(f"`{sub_line}`")
    else:
        # Calculates the range of lines to display
        start_index = max(0, current_line_index - context_lines)
        end_index = min(len(lyrics_lines), current_line_index + context_lines + 1)

        # Loop over the lines to display
        for i in range(start_index, end_index):
            line_obj = lyrics_lines[i]
            is_current_line_chunk = (i == current_line_index)

            # === THIS IS THE LOGIC THAT 100% FIXES THE BUG ===
            # We split the current lyric line into sub-lines
            sub_lines = clean(line_obj['text']).split('\n')

            for index, sub_line in enumerate(sub_lines):
                if not sub_line.strip(): continue

                # The "»" arrow only appears on the first sub-line of the current block
                prefix = "**»** " if is_current_line_chunk and index == 0 else ""

                display_parts.append(f"{prefix}`{sub_line}`")

    # We assemble everything and make sure not to exceed the Discord limit
    full_text = "\n".join(display_parts)
    return full_text[:4000]

# Create loading bar
def create_loading_bar(progress, width=10):
    filled = int(progress * width)
    unfilled = width - filled
    return '```[' + '█' * filled + '░' * unfilled + '] ' + f'{int(progress * 100)}%```'

# --- Platform URL Processors ---

# --- FINAL PROCESS_SPOTIFY_URL FUNCTION (Cascade Architecture) ---
async def process_spotify_url(url, interaction):
    """
    Processes a Spotify URL with a cascade architecture:
    1. Tries with the official API (spotipy) for speed and completeness.
    2. On failure (e.g., editorial playlist), falls back to the scraper (spotifyscraper).
    """
    guild_id = interaction.guild.id
    is_kawaii = get_mode(guild_id)
    clean_url = url.split('?')[0]

    # --- METHOD 1: OFFICIAL API (SPOTIPY) ---
    if sp:
        try:
            logger.info(f"Attempt 1: Official API (Spotipy) for {clean_url}")
            tracks_to_return = []
            loop = asyncio.get_event_loop()

            if 'playlist' in clean_url:
                results = await loop.run_in_executor(None, lambda: sp.playlist_items(clean_url, fields='items.track.name,items.track.artists.name,next', limit=100))
                while results:
                    for item in results['items']:
                        if item and item.get('track'):
                            track = item['track']
                            tracks_to_return.append((track['name'], track['artists'][0]['name']))
                    if results['next']:
                        results = await loop.run_in_executor(None, lambda: sp.next(results))
                    else:
                        results = None

            elif 'album' in clean_url:
                results = await loop.run_in_executor(None, lambda: sp.album_tracks(clean_url, limit=50))
                while results:
                    for track in results['items']:
                        tracks_to_return.append((track['name'], track['artists'][0]['name']))
                    if results['next']:
                        results = await loop.run_in_executor(None, lambda: sp.next(results))
                    else:
                        results = None

            elif 'track' in clean_url:
                track = await loop.run_in_executor(None, lambda: sp.track(clean_url))
                tracks_to_return.append((track['name'], track['artists'][0]['name']))

            elif 'artist' in clean_url:
                results = await loop.run_in_executor(None, lambda: sp.artist_top_tracks(clean_url))
                for track in results['tracks']:
                    tracks_to_return.append((track['name'], track['artists'][0]['name']))

            if not tracks_to_return:
                    raise ValueError("No tracks found via API.")

            logger.info(f"Success with Spotipy: {len(tracks_to_return)} tracks retrieved.")
            return tracks_to_return

        except Exception as e:
            logger.warning(f"Spotipy API failed for {clean_url} (Reason: {e}). Switching to plan B: SpotifyScraper.")

    # --- METHOD 2: FALLBACK (SPOTIFYSCRAPER) ---
    if spotify_scraper_client:
        try:
            logger.info(f"Attempt 2: Scraper (SpotifyScraper) for {clean_url}")
            tracks_to_return = []
            loop = asyncio.get_event_loop()

            if 'playlist' in clean_url:
                data = await loop.run_in_executor(None, lambda: spotify_scraper_client.get_playlist_info(clean_url))
                for track in data.get('tracks', []):
                    tracks_to_return.append((track.get('name', 'Unknown Title'), track.get('artists', [{}])[0].get('name', 'Unknown Artist')))

            elif 'album' in clean_url:
                data = await loop.run_in_executor(None, lambda: spotify_scraper_client.get_album_info(clean_url))
                for track in data.get('tracks', []):
                    tracks_to_return.append((track.get('name', 'Unknown Title'), track.get('artists', [{}])[0].get('name', 'Unknown Artist')))

            elif 'track' in clean_url:
                data = await loop.run_in_executor(None, lambda: spotify_scraper_client.get_track_info(clean_url))
                tracks_to_return.append((data.get('name', 'Unknown Title'), data.get('artists', [{}])[0].get('name', 'Unknown Artist')))

            if not tracks_to_return:
                raise SpotifyScraperError("The scraper could not find any tracks either.")

            logger.info(f"Success with SpotifyScraper: {len(tracks_to_return)} tracks retrieved (potentially limited).")
            return tracks_to_return

        # --- THIS IS THE CORRECTED ERROR HANDLING BLOCK ---
        except (SpotifyScraperError, spotipy.exceptions.SpotifyException) as e:
            logger.error(f"Both methods (API and Scraper) failed. Final error: {e}", exc_info=True)
            
            embed = Embed(
                title=get_messages("spotify_error_title", guild_id),
                description=get_messages("spotify_error_description_detailed", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
            return None
        # --- END OF CORRECTION ---
        except Exception as e: # General fallback for any other unexpected errors
            logger.error(f"An unexpected error occurred in the Spotify fallback: {e}", exc_info=True)
            embed = Embed(description=get_messages("spotify_error", guild_id), color=0xFFB6C1 if is_kawaii else discord.Color.red())
            await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
            return None

    logger.critical("No client (Spotipy or SpotifyScraper) is functional.")
    embed = Embed(description="Critical error: Spotify services are unreachable.", color=discord.Color.dark_red())
    await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
    return None
    
# Process Deezer URLs
async def process_deezer_url(url, interaction):
    guild_id = interaction.guild_id
    try:
        deezer_share_regex = re.compile(r'^(https?://)?(link\.deezer\.com)/s/.+$')
        if deezer_share_regex.match(url):
            logger.info(f"Detected Deezer share link: {url}. Resolving redirect...")
            response = requests.head(url, allow_redirects=True, timeout=10)
            response.raise_for_status()
            resolved_url = response.url
            logger.info(f"Resolved to: {resolved_url}")
            url = resolved_url

        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) > 1 and len(path_parts[0]) == 2:
            path_parts = path_parts[1:]
        if len(path_parts) < 2:
            raise ValueError("Invalid Deezer URL format")

        resource_type = path_parts[0]
        resource_id = path_parts[1].split('?')[0]

        base_api_url = "https://api.deezer.com"
        logger.info(f"Fetching Deezer {resource_type} with ID {resource_id} from URL {url}")

        tracks = []
        if resource_type == 'track':
            response = requests.get(f"{base_api_url}/track/{resource_id}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                raise Exception(f"Deezer API error: {data['error']['message']}")
            logger.info(f"Processing Deezer track: {data.get('title', 'Unknown Title')}")
            track_name = data.get('title', 'Unknown Title')
            artist_name = data.get('artist', {}).get('name', 'Unknown Artist')
            tracks.append((track_name, artist_name))

        elif resource_type == 'playlist':
            next_url = f"{base_api_url}/playlist/{resource_id}/tracks"
            total_tracks = 0
            fetched_tracks = 0

            while next_url:
                response = requests.get(next_url, timeout=10)
                response.raise_for_status()
                data = response.json()

                if 'error' in data:
                    raise Exception(f"Deezer API error: {data['error']['message']}")

                if not data.get('data'):
                    raise ValueError("No tracks found in the playlist or playlist is empty")

                for track in data['data']:
                    track_name = track.get('title', 'Unknown Title')
                    artist_name = track.get('artist', {}).get('name', 'Unknown Artist')
                    tracks.append((track_name, artist_name))

                fetched_tracks += len(data['data'])
                total_tracks = data.get('total', fetched_tracks)
                logger.info(f"Fetched {fetched_tracks}/{total_tracks} tracks from playlist {resource_id}")

                next_url = data.get('next')
                if next_url:
                    logger.info(f"Fetching next page: {next_url}")

            logger.info(f"Processing Deezer playlist: {data.get('title', 'Unknown Playlist')} with {len(tracks)} tracks")

        elif resource_type == 'album':
            response = requests.get(f"{base_api_url}/album/{resource_id}/tracks", timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                raise Exception(f"Deezer API error: {data['error']['message']}")
            if not data.get('data'):
                raise ValueError("No tracks found in the album or album is empty")
            logger.info(f"Processing Deezer album: {data.get('title', 'Unknown Album')}")
            for track in data['data']:
                track_name = track.get('title', 'Unknown Title')
                artist_name = track.get('artist', {}).get('name', 'Unknown Artist')
                tracks.append((track_name, artist_name))
            logger.info(f"Extracted {len(tracks)} tracks from album {resource_id}")

        elif resource_type == 'artist':
            response = requests.get(f"{base_api_url}/artist/{resource_id}/top?limit=10", timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                raise Exception(f"Deezer API error: {data['error']['message']}")
            if not data.get('data'):
                raise ValueError("No top tracks found for the artist")
            logger.info(f"Processing Deezer artist: {data.get('name', 'Unknown Artist')}")
            for track in data['data']:
                track_name = track.get('title', 'Unknown Title')
                artist_name = track.get('artist', {}).get('name', 'Unknown Artist')
                tracks.append((track_name, artist_name))
            logger.info(f"Extracted {len(tracks)} top tracks for artist {resource_id}")

        if not tracks:
            raise ValueError("No valid tracks found in the Deezer resource")

        logger.info(f"Successfully processed Deezer {resource_type} with {len(tracks)} tracks")
        return tracks

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching Deezer URL {url}: {e}")
        embed = Embed(
            description="Network error while retrieving Deezer data. Please try again later.",
            color=0xFFB6C1 if get_mode(guild_id) else discord.Color.red()
        )
        await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
        return None
    except ValueError as e:
        logger.error(f"Invalid Deezer data for URL {url}: {e}")
        embed = Embed(
            description=f"Error: {str(e)}",
            color=0xFFB6C1 if get_mode(guild_id) else discord.Color.red()
        )
        await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing Deezer URL {url}: {e}")
        embed = Embed(
            description=get_messages("deezer_error", guild_id),
            color=0xFFB6C1 if get_mode(guild_id) else discord.Color.red()
        )
        await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
        return None

# Process Apple Music URLs
async def process_apple_music_url(url, interaction):
    guild_id = interaction.guild.id
    logger.info(f"Starting processing for Apple Music URL: {url}")

    clean_url = url.split('?')[0]
    browser = None

    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
            )
            page = await context.new_page()

            await page.route("**/*.{png,jpg,jpeg,svg,woff,woff2}", lambda route: route.abort())
            logger.info("Optimization: Disabled loading of images and fonts.")

            logger.info("Navigating to the page with a 90 second timeout...")
            await page.goto(clean_url, wait_until="domcontentloaded", timeout=90000)
            logger.info("Page loaded. Extracting data...")

            tracks = []
            resource_type = 'unknown'
            path_parts = urlparse(clean_url).path.strip('/').split('/')
            
            if len(path_parts) > 1:
                if path_parts[1] in ['album', 'playlist']:
                    resource_type = path_parts[1]
                elif path_parts[1] == 'song':
                    resource_type = 'song'

            logger.info(f"Detected resource type: {resource_type}")

            if resource_type in ['album', 'playlist']:
                logger.info(f"Processing as {resource_type}, using row scraping method.")
                await page.wait_for_selector('div.songs-list-row', timeout=20000)
                main_artist_name = "Unknown Artist"
                try:
                    main_artist_el = await page.query_selector('.headings__subtitles a')
                    if main_artist_el:
                        main_artist_name = await main_artist_el.inner_text()
                except Exception:
                    logger.warning("Could not determine the main artist for the collection.")

                track_rows = await page.query_selector_all('div.songs-list-row')
                for row in track_rows:
                    try:
                        title_el = await row.query_selector('div.songs-list-row__song-name')
                        title = await title_el.inner_text() if title_el else "Unknown Title"

                        artist_elements = await row.query_selector_all('div.songs-list-row__by-line a')
                        if artist_elements:
                            artist_names = [await el.inner_text() for el in artist_elements]
                            artist = " & ".join(artist_names)
                        else:
                            artist = main_artist_name

                        if title != "Unknown Title":
                            tracks.append((title.strip(), artist.strip()))
                    except Exception as e:
                        logger.warning(f"Failed to extract a track row: {e}")

            elif resource_type == 'song':
                logger.info("Processing as single song, using JSON-LD method.")
                try:
                    json_ld_selector = 'script[id="schema:song"]'
                    await page.wait_for_selector(json_ld_selector, timeout=15000)
                    
                    json_ld_content = await page.locator(json_ld_selector).inner_text()
                    data = json.loads(json_ld_content)

                    title = data['audio']['name']
                    artist = data['audio']['byArtist'][0]['name']

                    if title and artist:
                        logger.info(f"Successfully extracted from JSON-LD: '{title}' by '{artist}'")
                        tracks.append((title.strip(), artist.strip()))
                    else:
                        raise ValueError("JSON-LD data is missing name or artist.")
                except Exception as e:
                    logger.warning(f"JSON-LD method failed ({e}). Falling back to HTML element scraping.")
                    title_selector = 'h1[data-testid="song-title"]'
                    artist_selector = 'span[data-testid="song-subtitle-artists"] a'
                    await page.wait_for_selector(title_selector, timeout=10000)
                    
                    title = await page.locator(title_selector).first.inner_text()
                    artist = await page.locator(artist_selector).first.inner_text()
                    
                    if title and artist:
                        logger.info(f"Successfully extracted from HTML fallback: '{title}' by '{artist}'")
                        tracks.append((title.strip(), artist.strip()))

            if not tracks:
                raise ValueError("No tracks could be extracted from the Apple Music resource.")

            logger.info(f"Success! {len(tracks)} track(s) extracted.")
            return tracks

    except Exception as e:
        logger.error(f"Error processing Apple Music URL {url}: {e}", exc_info=True)
        if 'page' in locals() and page and not page.is_closed():
            await page.screenshot(path="apple_music_scrape_failed.png")
            logger.info("Screenshot of the error saved.")
        
        embed = Embed(
            description=get_messages("apple_music_error", guild_id),
            color=0xFFB6C1 if get_mode(guild_id) else discord.Color.red()
        )
        try:
            if interaction and not interaction.is_expired():
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
        except Exception as send_error:
            logger.error(f"Unable to send error message: {send_error}")
        return None
    finally:
        if browser:
            await browser.close()
            logger.info("Playwright (Apple Music) browser closed successfully.")
                                                            
# Process Tidal URLs
async def process_tidal_url(url, interaction):
    guild_id = interaction.guild_id

    async def load_and_extract_all_tracks(page):
        logger.info("Reliable loading begins (track by track)...")
        total_tracks_expected = 0
        try:
            meta_item_selector = 'span[data-test="grid-item-meta-item-count"]'
            meta_text = await page.locator(meta_item_selector).first.inner_text(timeout=3000)
            total_tracks_expected = int(re.search(r'\d+', meta_text).group())
            logger.info(f"Goal: Extract {total_tracks_expected} tracks.")
        except Exception:
            logger.warning("Unable to determine the total number of tracks.")
            total_tracks_expected = 0
        track_row_selector = 'div[data-track-id]'
        all_tracks = []
        seen_track_ids = set()
        stagnation_counter = 0
        max_loops = 500
        for i in range(max_loops):
            if total_tracks_expected > 0 and len(all_tracks) >= total_tracks_expected:
                logger.info("All expected leads have been found. Early shutdown.")
                break
            track_elements = await page.query_selector_all(track_row_selector)
            if not track_elements and i > 0: break
            new_tracks_found_in_loop = False
            for element in track_elements:
                track_id = await element.get_attribute('data-track-id')
                if track_id and track_id not in seen_track_ids:
                    new_tracks_found_in_loop = True
                    seen_track_ids.add(track_id)
                    try:
                        title_el = await element.query_selector('span._titleText_51cccae, span[data-test="table-cell-title"]')
                        artist_el = await element.query_selector('a._item_39605ae, a[data-test="grid-item-detail-text-title-artist"]')
                        if title_el and artist_el:
                            title = (await title_el.inner_text()).split("<span>")[0].strip()
                            artist = await artist_el.inner_text()
                            if title and artist: all_tracks.append((title, artist))
                    except Exception: continue
            if not new_tracks_found_in_loop and i > 1:
                stagnation_counter += 1
                if stagnation_counter >= 5:
                    logger.info("Stable stagnation. End of process.")
                    break
            else: stagnation_counter = 0
            if track_elements:
                await track_elements[-1].scroll_into_view_if_needed(timeout=10000)
                await asyncio.sleep(0.75)
        logger.info(f"Process completed. Final total of unique tracks extracted: {len(all_tracks)}")
        return list(dict.fromkeys(all_tracks))

    browser = None  # Initialize the browser to None
    try:
        clean_url = url.split('?')[0]
        parsed_url = urlparse(clean_url)
        path_parts = parsed_url.path.strip('/').split('/')

        resource_type = None
        if 'playlist' in path_parts: resource_type = 'playlist'
        elif 'album' in path_parts: resource_type = 'album'
        elif 'mix' in path_parts: resource_type = 'mix'
        elif 'track' in path_parts: resource_type = 'track'
        elif 'video' in path_parts: resource_type = 'video'

        if resource_type is None:
            raise ValueError("Tidal URL not supported.")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            await page.goto(clean_url, wait_until="domcontentloaded")
            logger.info(f"Navigate to Tidal URL ({resource_type}): {clean_url}")

            await asyncio.sleep(3)
            unique_tracks = []

            if resource_type in ['playlist', 'album', 'mix']:
                unique_tracks = await load_and_extract_all_tracks(page)

            elif resource_type == 'track' or resource_type == 'video':
                logger.info(f"Extracting a single media ({resource_type})...")
                try:
                    await page.wait_for_selector('div[data-test="artist-profile-header"], div[data-test="footer-player"]', timeout=10000)
                    title_selector = 'span[data-test="now-playing-track-title"], h1[data-test="title"]'
                    artist_selector = 'a[data-test="grid-item-detail-text-title-artist"]'
                    title = await page.locator(title_selector).first.inner_text(timeout=5000)
                    artist = await page.locator(artist_selector).first.inner_text(timeout=5000)

                    if not title or not artist:
                        raise ValueError("Missing title or artist.")

                    logger.info(f"Unique media found: {title.strip()} - {artist.strip()}")
                    unique_tracks = [(title.strip(), artist.strip())]

                except Exception as e:
                    logger.warning(f"Direct extraction method failed ({e}), attempting with page title...")
                    try:
                        page_title = await page.title()
                        title, artist = "", ""
                        if " - " in page_title:
                            parts = page_title.split(' - ')
                            artist, title = parts[0], parts[1].split(' on TIDAL')[0]
                        elif " by " in page_title:
                            parts = page_title.split(' by ')
                            title, artist = parts[0], parts[1].split(' on TIDAL')[0]

                        if not title or not artist: raise ValueError("The page title format is unknown.")

                        logger.info(f"Unique media found via page title: {title.strip()} - {artist.strip()}")
                        unique_tracks = [(title.strip(), artist.strip())]
                    except Exception as fallback_e:
                        await page.screenshot(path=f"tidal_{resource_type}_extraction_failed.png")
                        raise ValueError(f"All extraction methods failed. Final error: {fallback_e}")

            if not unique_tracks:
                raise ValueError("No tracks could be retrieved from the Tidal resource.")

            return unique_tracks

    except Exception as e:
        logger.error(f"Major error in process_tidal_url for {url}: {e}")
        if interaction:
                embed = Embed(description=get_messages("tidal_error", guild_id), color=0xFFB6C1 if get_mode(guild_id) else discord.Color.red())
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
        return None
    finally:
        if browser:
            await browser.close()
            logger.info("Playwright (Tidal) browser closed properly.")

async def process_amazon_music_url(url, interaction):
    guild_id = interaction.guild_id
    logger.info(f"Launching unified processing for Amazon Music URL: {url}")

    is_album = "/albums/" in url
    is_playlist = "/playlists/" in url or "/user-playlists/" in url
    is_track = "/tracks/" in url

    browser = None  # Initialize the browser to None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            logger.info("Page loaded. Cookie management.")

            try:
                await page.click('music-button:has-text("Accepter les cookies")', timeout=7000)
                logger.info("Cookie banner accepted.")
            except Exception:
                logger.info("No cookie banner found.")

            tracks = []

            if is_album or is_track:
                page_type = "Album" if is_album else "Track"
                logger.info(f"Page of type '{page_type}' detected. Using JSON extraction method.")

                selector = 'script[type="application/ld+json"]'
                await page.wait_for_selector(selector, state='attached', timeout=20000)

                json_ld_scripts = await page.locator(selector).all_inner_texts()

                found_data = False
                for script_content in json_ld_scripts:
                    data = json.loads(script_content)
                    if data.get('@type') == 'MusicAlbum' or (is_album and 'itemListElement' in data):
                        album_artist = data.get('byArtist', {}).get('name', 'Unknown Artist')
                        for item in data.get('itemListElement', []):
                            track_name = item.get('name')
                            track_artist = item.get('byArtist', {}).get('name', album_artist)
                            if track_name and track_artist:
                                tracks.append((track_name, track_artist))
                        found_data = True
                        break
                    elif data.get('@type') == 'MusicRecording':
                        track_name = data.get('name')
                        track_artist = data.get('byArtist', {}).get('name', 'Unknown Artist')
                        if track_name and track_artist:
                            tracks.append((track_name, track_artist))
                        found_data = True
                        break

                if not found_data:
                    raise ValueError(f"No data of type 'MusicAlbum' or 'MusicRecording' found in JSON-LD tags.")

            elif is_playlist:
                logger.info("'Playlist' type page detected. Using fast pre-virtualization extraction.")
                try:
                    await page.wait_for_selector("music-image-row[primary-text]", timeout=20000)
                    logger.info("Tracklist detected. Waiting 3.5 seconds for initial load.")
                    await asyncio.sleep(3.5)
                except Exception as e:
                    raise ValueError(f"Unable to detect initial tracklist: {e}")

                js_script_playlist = """
                () => {
                    const tracksData = [];
                    const rows = document.querySelectorAll('music-image-row[primary-text]');
                    rows.forEach(row => {
                        const title = row.getAttribute('primary-text');
                        const artist = row.getAttribute('secondary-text-1');
                        const indexEl = row.querySelector('span.index');
                        const index = indexEl ? parseInt(indexEl.innerText.trim(), 10) : null;
                        if (title && artist && index !== null && !isNaN(index)) {
                            tracksData.push({ index: index, title: title.trim(), artist: artist.trim() });
                        }
                    });
                    tracksData.sort((a, b) => a.index - b.index);
                    return tracksData.map(t => ({ title: t.title, artist: t.artist }));
                }
                """
                tracks_data = await page.evaluate(js_script_playlist)
                tracks = [(track['title'], track['artist']) for track in tracks_data]

            else:
                raise ValueError("Amazon Music URL not recognized (neither album, nor playlist, nor track).")

            if not tracks:
                raise ValueError("No tracks could be extracted from the page.")

            logger.info(f"Processing complete. {len(tracks)} track(s) found. First track: {tracks[0]}")
            return tracks

    except Exception as e:
        logger.error(f"Final error in process_amazon_music_url for {url}: {e}", exc_info=True)
        if 'page' in locals() and page and not page.is_closed():
                await page.screenshot(path="amazon_music_scrape_failed.png")
                logger.info("Screenshot of the error saved.")

        embed = Embed(description=get_messages("amazon_music_error", guild_id), color=0xFFB6C1 if get_mode(guild_id) else discord.Color.red())
        try:
            if interaction and not interaction.is_expired():
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
        except Exception as send_error:
            logger.error(f"Unable to send error message: {send_error}")
        return None
    finally:
        if browser:
            await browser.close()
            logger.info("Playwright (Amazon Music) browser closed successfully.")

# --- Search & Extraction Helpers ---

# Normalize strings for search queries
def sanitize_query(query):
    query = re.sub(r'[\x00-\x1F\x7F]', '', query)  # Remove control chars
    query = re.sub(r'\s+', ' ', query).strip()  # Normalize spaces
    return query

# Async yt-dlp info extraction
async def extract_info_async(ydl_opts, query, loop=None):
    if loop is None:
        loop = asyncio.get_running_loop()

    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)

    return await loop.run_in_executor(None, extract)

# YouTube Mix and SoundCloud Stations utilities
def get_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname in ('youtube.com', 'www.youtube.com', 'youtu.be'):
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
    return 
    
# --- NEW --- Helper function to parse yt-dlp errors into user-friendly messages
def parse_yt_dlp_error(error_string: str) -> tuple[str, str, str]:
    """
    Parses a yt-dlp error string to find a known cause.
    Returns a tuple of (emoji, title_key, description_key).
    """
    error_lower = error_string.lower()
    if "sign in to confirm your age" in error_lower or "age-restricted" in error_lower:
        return ("🔞", "error_title_age_restricted", "error_desc_age_restricted")
    if "private video" in error_lower:
        return ("🔒", "error_title_private", "error_desc_private")
    if "video is unavailable" in error_lower:
        return ("❓", "error_title_unavailable", "error_desc_unavailable")
    # Default fallback for other access errors
    return ("🚫", "error_title_generic", "error_desc_generic")

# ==============================================================================
# 4. CORE AUDIO & PLAYBACK LOGIC
# ==============================================================================

async def handle_playback_error(guild_id: int, error: Exception):
    """
    Handles unexpected errors during playback, informs the user,
    and provides instructions for reporting the bug.
    """
    music_player = get_player(guild_id)
    if not music_player.text_channel:
        logger.error(f"Cannot report error in guild {guild_id}, no text channel available.")
        return

    tb_str = ''.join(traceback.format_exception(type(error), value=error, tb=error.__traceback__))
    logger.error(f"Unhandled playback error in guild {guild_id}:\n{tb_str}")

    is_kawaii = get_mode(guild_id)
    embed = Embed(
        title=get_messages("critical_error_title", guild_id),
        description=get_messages("critical_error_description", guild_id),
        color=0xFF9AA2 if is_kawaii else discord.Color.red()
    )
    embed.add_field(
        name=get_messages("critical_error_report_field", guild_id),
        value=get_messages("critical_error_report_value", guild_id),
        inline=False
    )
    error_details = f"URL: {music_player.current_url}\nError: {str(error)[:500]}"
    embed.add_field(
        name=get_messages("critical_error_details_field", guild_id),
        value=f"```\n{error_details}\n```",
        inline=False
    )
    embed.set_footer(text="Your help is appreciated!")

    try:
        await music_player.text_channel.send(embed=embed, silent=SILENT_MESSAGES)
    except discord.Forbidden:
        logger.warning(f"Failed to send error report to guild {guild_id}: Missing Permissions.")
    except Exception as e:
        logger.error(f"Failed to send error report embed to guild {guild_id}: {e}")

    music_player.current_task = None
    music_player.current_info = None
    music_player.current_url = None
    while not music_player.queue.empty():
        music_player.queue.get_nowait()

    if music_player.voice_client:
        await music_player.voice_client.disconnect()
        music_players[guild_id] = MusicPlayer()
        logger.info(f"Player for guild {guild_id} has been reset and disconnected due to a critical error.")

# ==============================================================================
# 4. CORE AUDIO & PLAYBACK LOGIC
# ==============================================================================

async def play_audio(guild_id, seek_time=0, is_a_loop=False):
    music_player = get_player(guild_id)

    if music_player.voice_client and music_player.voice_client.is_playing() and not is_a_loop and not seek_time > 0:
        return

    async def after_playing(error, song_info):
        if error:
            logger.error(f'Error after playing in guild {guild_id}: {error}')
            
        if not music_player.voice_client or not music_player.voice_client.is_connected():
            logger.info(f"[{guild_id}] after_playing: Canceling next play_audio call because the voice client is no longer connected.")
            return

        if music_player.is_reconnecting:
            return

        if music_player.seek_info is not None:
            new_seek_time = music_player.seek_info
            music_player.seek_info = None
            await play_audio(guild_id, seek_time=new_seek_time, is_a_loop=True)
            return

        if not song_info:
            await play_audio(guild_id, is_a_loop=False)
            return

        if music_player.loop_current:
            await play_audio(guild_id, is_a_loop=True)
        else:
            track_to_requeue = create_queue_item_from_info(song_info)
            if _24_7_active.get(guild_id, False) and not music_player.autoplay_enabled:
                await music_player.queue.put(track_to_requeue)
                logger.info(f"[{guild_id}] 24/7 Normal: Looping track '{track_to_requeue.get('title')}' to the end of the queue.")
            
            await play_audio(guild_id, is_a_loop=False)

    try:
        if music_player.is_resuming_live:
            logger.info(f"[{guild_id}] Executing live stream resync mission.")
            music_player.is_resuming_live = False
            seek_time = 0.1
            is_a_loop = True
        
        elif is_a_loop or seek_time > 0:
            logger.info(f"[{guild_id}] Executing replay mission (loop or seek).")
            pass

        else:
            logger.info(f"[{guild_id}] Executing 'play next' mission.")
            if music_player.lyrics_task and not music_player.lyrics_task.done():
                music_player.lyrics_task.cancel()
            
            music_player.is_current_live = False
            
            if music_player.queue.empty():
                is_kawaii = get_mode(guild_id)
                is_24_7_on = _24_7_active.get(guild_id, False)

                if is_24_7_on and not music_player.autoplay_enabled and music_player.radio_playlist:
                    for track_info_radio in music_player.radio_playlist:
                        await music_player.queue.put(track_info_radio)
                
                elif (is_24_7_on and music_player.autoplay_enabled) or music_player.autoplay_enabled:
                    music_player.suppress_next_now_playing = False
                    seed_url = None
                    
                    # --- START OF THE NEW AND FINAL AUTOPLAY LOGIC ---
                    is_recommendable = False
                    if music_player.current_info and music_player.current_url:
                        if "youtube.com" in music_player.current_url or "youtu.be" in music_player.current_url or "soundcloud.com" in music_player.current_url:
                            is_recommendable = True

                    if is_recommendable:
                        seed_url = music_player.current_url
                        # Send the "Adding songs" message ONLY when we can act immediately
                        if music_player.text_channel:
                            try:
                                await music_player.text_channel.send(embed=Embed(description=get_messages("autoplay_added", guild_id), color=0xC7CEEA if is_kawaii else discord.Color.blue()), silent=SILENT_MESSAGES)
                            except discord.Forbidden: pass
                    else:
                        # Logic for when the source is a file or a direct link
                        if music_player.text_channel and music_player.current_info:
                            try:
                                # Determine which notice to show
                                if music_player.current_info.get('source_type') == 'file':
                                    notice_key = "autoplay_file_notice"
                                else:
                                    notice_key = "autoplay_direct_link_notice" # Use the new key
                                
                                await music_player.text_channel.send(embed=Embed(description=get_messages(notice_key, guild_id), color=0xFFB6C1 if is_kawaii else discord.Color.blue()), silent=SILENT_MESSAGES)
                            except discord.Forbidden: pass
                        
                        source_list = music_player.radio_playlist if is_24_7_on and music_player.radio_playlist else music_player.history
                        for track in reversed(source_list):
                            track_url = track.get('url')
                            if track_url and ("youtube.com" in track_url or "youtu.be" in track_url or "soundcloud.com" in track_url):
                                seed_url = track_url
                                break
                    # --- END OF THE NEW AND FINAL AUTOPLAY LOGIC ---
                    
                    if seed_url:
                        # The "adding songs" message has been moved, so we proceed directly
                        if "youtube.com" in seed_url or "youtu.be" in seed_url:
                            mix_playlist_url = get_mix_playlist_url(seed_url)
                            if mix_playlist_url:
                                try:
                                    info = await extract_info_async({"extract_flat": True, "quiet": True, "noplaylist": False}, mix_playlist_url)
                                    if info.get("entries"):
                                        current_video_id = get_video_id(seed_url)
                                        for entry in info["entries"]:
                                            if entry and get_video_id(entry.get("url", "")) != current_video_id:
                                                await music_player.queue.put({'url': entry.get('url'), 'title': entry.get('title', 'Unknown Title'), 'webpage_url': entry.get('webpage_url', entry.get('url')), 'is_single': True})
                                except Exception as e: logger.error(f"YouTube Mix Error for autoplay: {e}")
                        elif "soundcloud.com" in seed_url:
                            track_id = get_soundcloud_track_id(seed_url)
                            station_url = get_soundcloud_station_url(track_id)
                            if station_url:
                                try:
                                    info = await extract_info_async({"extract_flat": True, "quiet": True, "noplaylist": False}, station_url)
                                    if info.get("entries") and len(info.get("entries")) > 1:
                                        for entry in info["entries"][1:]:
                                            if entry: await music_player.queue.put({'url': entry.get('url'), 'title': entry.get('title', 'Unknown Title'), 'webpage_url': entry.get('webpage_url', entry.get('url')), 'is_single': True})
                                except Exception as e: logger.error(f"SoundCloud Station Error for autoplay: {e}")

                if music_player.queue.empty():
                    music_player.current_info = None
                    music_player.current_task = None
                    if not _24_7_active.get(guild_id, False):
                        await asyncio.sleep(60)
                        if music_player.voice_client and not music_player.voice_client.is_playing() and len(music_player.voice_client.channel.members) == 1:
                            await music_player.voice_client.disconnect()
                    return
            
            track_info = await music_player.queue.get()
            if track_info.pop('skip_now_playing', False):
                music_player.suppress_next_now_playing = True
            if not music_player.loop_current:
                 music_player.history.append(track_info)
            music_player.current_url = track_info['url']
            music_player.last_was_single = track_info.get('is_single', True)
            music_player.current_info = track_info

        if not music_player.voice_client or not music_player.voice_client.is_connected() or not music_player.current_info:
            logger.warning(f"[{guild_id}] Play audio called but a condition was not met (no vc or no current_info). Aborting.")
            return

        active_filters = server_filters.get(guild_id, set())
        filter_chain = ",".join([AUDIO_FILTERS[f] for f in active_filters if f in AUDIO_FILTERS]) if active_filters else ""
        music_player.active_filter = filter_chain if filter_chain else None
        
        audio_url = None
        if music_player.current_info.get('source_type') == 'file':
            audio_url = music_player.current_url
            music_player.current_info['webpage_url'] = None
        else:
            ydl_opts_play = {"format": "bestaudio[acodec=opus]/bestaudio/best", "quiet": True, "no_warnings": True, "no_color": True, "socket_timeout": 10}

            try:
                original_track_info = music_player.current_info.copy()
                full_playback_info = await extract_info_async(ydl_opts_play, music_player.current_url)
                final_info = {**original_track_info, **full_playback_info}
                
                new_title = full_playback_info.get("title", "")
                if ("video #" in new_title or "AGB video" in new_title) and original_track_info.get("title"):
                    final_info["title"] = original_track_info["title"]

                music_player.current_info = final_info
                audio_url = final_info["url"] 
                music_player.is_current_live = final_info.get('is_live', False) or final_info.get('live_status') == 'is_live'

            except yt_dlp.utils.DownloadError as e:
                if music_player.text_channel:
                    try:
                        is_kawaii = get_mode(guild_id)
                        emoji, title_key, desc_key = parse_yt_dlp_error(str(e))
                        embed = Embed(title=f'{emoji} Playback Failed', description=get_messages(desc_key, guild_id), color=0xFF9AA2 if is_kawaii else discord.Color.orange())
                        embed.add_field(name="Affected URL", value=f"`{music_player.current_url}`")
                        await music_player.text_channel.send(embed=embed, silent=SILENT_MESSAGES)
                    except discord.Forbidden: pass
                music_player.current_task = bot.loop.create_task(play_audio(guild_id))
                return
        
        if not audio_url:
            music_player.current_task = bot.loop.create_task(play_audio(guild_id))
            return
            
        ffmpeg_options = {}
        if music_player.current_info.get('source_type') == 'file':
            ffmpeg_options = {"options": "-vn"}
        else:
            ffmpeg_options = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}

        if seek_time > 0:
            ffmpeg_options["before_options"] = f"-ss {seek_time} {ffmpeg_options.get('before_options', '')}".strip()

        if music_player.active_filter:
            ffmpeg_options["options"] = f"{ffmpeg_options.get('options', '')} -af \"{music_player.active_filter}\"".strip()

        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
        
        info_for_after = music_player.current_info.copy()
        callback = lambda e: bot.loop.create_task(after_playing(e, info_for_after))
        
        try:
            if music_player.voice_client and not music_player.voice_client.is_playing():
                 music_player.voice_client.play(source, after=callback)
            else:
                logger.warning(f"[{guild_id}] Race condition detected in play_audio. Ignored redundant play call.")
                source.cleanup()
                return
        except discord.errors.ClientException as e:
            if "Already playing audio" in str(e):
                logger.warning(f"[{guild_id}] Gracefully handled 'Already playing audio' exception.")
                source.cleanup()
                return
            else:
                await handle_playback_error(guild_id, e)
                return

        music_player.start_time = seek_time
        music_player.playback_started_at = time.time()
        
        if music_player.suppress_next_now_playing:
            music_player.suppress_next_now_playing = False  
        
        elif not is_a_loop and seek_time == 0:
            is_kawaii = get_mode(guild_id)
            title = music_player.current_info.get("title", "Unknown Title")
            
            description_text = ""
            if music_player.current_info.get('source_type') == 'file':
                description_text = f"💿 `{title}`"
            else:
                webpage_url = music_player.current_info.get("webpage_url", music_player.current_url)
                description_text = get_messages("now_playing_description", guild_id).format(title=title, url=webpage_url)
            
            embed = Embed(
                title=get_messages("now_playing_title", guild_id),
                description=description_text, 
                color=0xC7CEEA if is_kawaii else discord.Color.green()
            )

            if music_player.current_info.get("thumbnail"):
                embed.set_thumbnail(url=music_player.current_info["thumbnail"])
            
            if music_player.text_channel:
                try:
                    await music_player.text_channel.send(embed=embed, silent=SILENT_MESSAGES)
                except discord.Forbidden:
                    logger.warning(f"Failed to send 'Now Playing' message to guild {guild_id}: Missing Permissions.")
                except Exception as e:
                    logger.error(f"Failed to send 'Now Playing' message to guild {guild_id}: {e}")

    except Exception as e:
        await handle_playback_error(guild_id, e)

async def update_karaoke_task(guild_id: int):
    """Background task for karaoke mode, manages filters and speed."""
    music_player = get_player(guild_id)
    last_line_index = -1
    # We add a flag to know if the footer has already been removed
    footer_has_been_removed = False

    while music_player.voice_client and music_player.voice_client.is_connected():
        try:
            if not music_player.voice_client.is_playing():
                await asyncio.sleep(0.5)
                continue

            real_elapsed_time = (time.time() - music_player.playback_started_at)
            effective_time_in_song = music_player.start_time + (real_elapsed_time * music_player.playback_speed)

            current_line_index = -1
            for i, line in enumerate(music_player.synced_lyrics):
                if effective_time_in_song * 1000 >= line['time']:
                    current_line_index = i
                else:
                    break

            if current_line_index != last_line_index:
                last_line_index = current_line_index
                new_description = format_lyrics_display(music_player.synced_lyrics, current_line_index)

                if music_player.lyrics_message and music_player.lyrics_message.embeds:
                    new_embed = music_player.lyrics_message.embeds[0]
                    new_embed.description = new_description

                    # --- START OF MODIFICATION ---
                    # If the footer has not been removed yet, we do it now.
                    if not footer_has_been_removed:
                        # This line removes the embed's footer
                        new_embed.set_footer(text=None)
                        # We set the flag to True so we never do it again for this song
                        footer_has_been_removed = True
                    # --- END OF MODIFICATION ---

                    await music_player.lyrics_message.edit(embed=new_embed)

            await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in karaoke task: {e}")
            break

    if music_player.lyrics_message:
        try:
            await music_player.lyrics_message.edit(content="*Karaoke session finished!*", embed=None, view=None)
        except discord.NotFound:
            pass

    music_player.lyrics_task = None
    music_player.lyrics_message = None

# ==============================================================================
# 5. DISCORD SLASH COMMANDS
# ==============================================================================

@bot.tree.command(name="lyrics", description="Get song lyrics from Genius.")
async def lyrics(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    music_player = get_player(guild_id)

    if not music_player.voice_client or not music_player.voice_client.is_playing() or not music_player.current_info:
        return await interaction.response.send_message("No music is currently playing.", silent=SILENT_MESSAGES, ephemeral=True)

    await interaction.response.defer()
    # We ONLY search for lyrics on Genius
    await fetch_and_display_genius_lyrics(interaction)

@bot.tree.command(name="karaoke", description="Start a synced karaoke-style lyrics display.")
async def karaoke(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    music_player = get_player(guild_id)
    is_kawaii = get_mode(guild_id)

    if not music_player.voice_client or not music_player.voice_client.is_playing() or not music_player.current_info:
        return await interaction.response.send_message("No music is currently playing.", silent=SILENT_MESSAGES, ephemeral=True)

    if music_player.lyrics_task and not music_player.lyrics_task.done():
        return await interaction.response.send_message("Lyrics are already being displayed!", silent=SILENT_MESSAGES, ephemeral=True)

    async def proceed_with_karaoke():
        if not interaction.response.is_done():
            await interaction.response.defer()

        clean_title, artist_name = get_cleaned_song_info(music_player.current_info)
        loop = asyncio.get_running_loop()
        lrc = None

        # Attempt 1: Precise search
        try:
            precise_query = f"{clean_title} {artist_name}"
            logger.info(f"Attempting precise synced lyrics search: '{precise_query}'")
            lrc = await asyncio.wait_for(
                loop.run_in_executor(None, syncedlyrics.search, precise_query),
                timeout=7.0
            )
        except (asyncio.TimeoutError, Exception):
            logger.warning("Precise synced search failed or timed out.")

        # Attempt 2: Broad search
        if not lrc:
            try:
                logger.info(f"Trying broad search: '{clean_title}'")
                lrc = await asyncio.wait_for(
                    loop.run_in_executor(None, syncedlyrics.search, clean_title),
                    timeout=7.0
                )
            except (asyncio.TimeoutError, Exception):
                logger.warning("Broad synced search also failed or timed out.")

        # --- CORRECTED LOGIC ---
        # First, try to parse the lyrics if a result was found
        lyrics_lines = []
        if lrc:
            lyrics_lines = [{'time': int(m.group(1))*60000 + int(m.group(2))*1000 + int(m.group(3)), 'text': m.group(4).strip()} for line in lrc.splitlines() if (m := re.match(r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)', line))]

        # Now, a SINGLE check handles all failures (not found OR bad format)
        if not lyrics_lines:
            error_title = get_messages("karaoke_not_found_title", guild_id)
            error_desc = get_messages("karaoke_not_found_description", guild_id).format(query=f"{clean_title} {artist_name}")

            error_embed = Embed(
                title=error_title,
                description=error_desc,
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )

            view = KaraokeRetryView(
                original_interaction=interaction,
                suggested_query=clean_title,
                guild_id=guild_id
            )
            # Use followup.send because the interaction is already deferred
            await interaction.followup.send(silent=SILENT_MESSAGES,embed=error_embed, view=view)
            return
        # --- END OF CORRECTION ---

        # If we get here, lyrics_lines is valid. Proceed with karaoke.
        music_player.synced_lyrics = lyrics_lines
        embed = Embed(title=f"🎤 Karaoke for {clean_title}", description="Starting karaoke...", color=0xC7CEEA if is_kawaii else discord.Color.blue())

        lyrics_message = await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, wait=True)
        music_player.lyrics_message = lyrics_message
        music_player.lyrics_task = asyncio.create_task(update_karaoke_task(guild_id))

    # --- Warning logic (unchanged) ---
    if guild_id in karaoke_disclaimer_shown:
        await proceed_with_karaoke()
    else:
        warning_embed = Embed(
            title=get_messages("karaoke_warning_title", guild_id),
            description=get_messages("karaoke_warning_description", guild_id),
            color=0xFFB6C1 if is_kawaii else discord.Color.orange()
        )
        view = KaraokeWarningView(interaction, karaoke_coro=proceed_with_karaoke)

        button_label = get_messages("karaoke_warning_button", guild_id)
        view.children[0].label = button_label

        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=warning_embed, view=view)

# /kaomoji command
@bot.tree.command(name="kaomoji", description="Enable/disable kawaii mode")
@app_commands.default_permissions(administrator=True)
async def toggle_kawaii(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    kawaii_mode[guild_id] = not get_mode(guild_id)
    state = get_messages("kawaii_state_enabled", guild_id) if kawaii_mode[guild_id] else get_messages("kawaii_state_disabled", guild_id)

    embed = Embed(
        description=get_messages("kawaii_toggle", guild_id).format(state=state),
        color=0xFFB6C1 if kawaii_mode[guild_id] else discord.Color.blue()
    )
    await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)

@bot.tree.command(name="play", description="Play a link or search for a song")
@app_commands.describe(query="Link or title of the song/video to play")
async def play(interaction: discord.Interaction, query: str):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    await interaction.response.defer()

    voice_client = await ensure_voice_connection(interaction)
    if not voice_client:
        return
    
    spotify_regex = re.compile(r'^(https?://)?(open\.spotify\.com)/.+$')
    deezer_regex = re.compile(r'^(https?://)?((www\.)?deezer\.com/(?:[a-z]{2}/)?(track|playlist|album|artist)/.+|(link\.deezer\.com)/s/.+)$')
    soundcloud_regex = re.compile(r'^(https?://)?(www\.)?(soundcloud\.com)/.+$')
    youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
    ytmusic_regex = re.compile(r'^(https?://)?(music\.youtube\.com)/.+$')
    bandcamp_regex = re.compile(r'^(https?://)?([^\.]+)\.bandcamp\.com/.+$')
    apple_music_regex = re.compile(r'^(https?://)?(music\.apple\.com)/.+$')
    tidal_regex = re.compile(r'^(https?://)?(www\.)?tidal\.com/.+$')
    amazon_music_regex = re.compile(r'^(https?://)?(music\.amazon\.(fr|com|co\.uk|de|es|it|jp))/.+$')
    direct_link_regex = re.compile(r'^(https?://).+\.(mp3|wav|ogg|m4a|mp4|webm|flac)(\?.+)?$', re.IGNORECASE)


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

            search_query = f"ytsearch:{sanitized_query}"
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
                        logger.warning(f"Skipping unavailable video for {sanitized_query}: {e}")
                        continue
                logger.warning(f"No accessible videos in top results for {sanitized_query}")

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
                ydl_opts_full = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "no_color": True,
                    "socket_timeout": 10,
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
                queue_item = {
                    'url': video_url,
                    'title': video.get('title', track_name),
                    'webpage_url': video_url,
                    'thumbnail': video.get('thumbnail'),
                    'is_single': True,
                    'skip_now_playing': True
                }
                await music_player.queue.put(queue_item)
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{video.get('title', track_name)}]({video_url})",
                    color=0xC7CEEA if is_kawaii else discord.Color.blue()
                )
                if video.get("thumbnail"):
                    embed.set_thumbnail(url=video["thumbnail"])
                if is_kawaii:
                    embed.set_footer(text="☆⌒(≧▽° )")
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            except Exception as e:
                logger.error(f"Spotify conversion error for {query}: {e}")
                embed = Embed(
                    description=get_messages("search_error", guild_id),
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                try:
                    await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
                except discord.errors.NotFound:
                    logger.warning(f"Interaction expired for single Spotify track error. Sending public message.")
                    await interaction.channel.send(content=f"{interaction.user.mention}, an error occurred.", embed=embed, silent=SILENT_MESSAGES)
        else:
            embed = Embed(
                title="Spotify playlist processing",
                description="Starting...",
                color=0xFFB6C1 if is_kawaii else discord.Color.blue()
            )
            message = await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)

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
                            # result[2] is track_name, result[3] is artist_name
                            failed_tracks.append(f"{result[2]} by {result[3]}")
                    else:
                        # We get all the info
                        _, video_url, track_name, artist_name = result
                        
                        # We create the object for the queue with a TEMPORARY title
                        queue_item = {
                            'url': video_url,
                            'title': f"{track_name} - {artist_name}", # The temporary title!
                            'webpage_url': video_url,
                            'is_single': False
                        }
                        await music_player.queue.put(queue_item)
                    processed += 1

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

            logger.info(f"Spotify playlist processed: {processed - failed} tracks added, {failed} failed")

            if processed - failed == 0:
                embed = Embed(
                    description="No tracks could be added.",
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

            if not music_player.hydration_task or music_player.hydration_task.done():
                logger.info(f"[{guild_id}] Spawning background hydration task for the queue.")
                music_player.hydration_task = bot.loop.create_task(background_queue_hydrator(guild_id))            

    elif deezer_regex.match(query):
        logger.info(f"Processing Deezer URL: {query}")
        deezer_tracks = await process_deezer_url(query, interaction)
        if not deezer_tracks:
            logger.warning(f"No tracks returned for Deezer URL: {query}")
            embed = Embed(
                description="No Deezer tracks could be processed. Check the URL or try again.",
                color=0xFFB6C1 if is_kawaii else discord.Color.red()
            )
            await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
            return

        if len(deezer_tracks) == 1:
            track_name, artist_name = deezer_tracks[0]
            query = f"{track_name} {artist_name}"
            logger.info(f"Searching YouTube for single Deezer track: {query}")
            try:
                cache_key = sanitize_query(query).lower()
                ydl_opts_full = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "no_color": True,
                    "socket_timeout": 10,
                }
                sanitized_query = sanitize_query(query)
                search_query = f"ytsearch:{sanitized_query}"
                info = await extract_info_async(ydl_opts_full, search_query)
                video = info["entries"][0] if "entries" in info and info["entries"] else None
                if not video:
                    raise Exception(f"No YouTube results found for {sanitized_query}")
                video_url = video.get("webpage_url", video.get("url"))
                if not video_url:
                    raise KeyError("No valid URL found in video metadata")
                logger.info(f"Found YouTube URL for Deezer track: {video_url}")
                url_cache[cache_key] = video_url
                queue_item = {
                    'url': video_url,
                    'title': video.get('title', track_name),
                    'webpage_url': video_url,
                    'thumbnail': video.get('thumbnail'),
                    'is_single': True,
                    'skip_now_playing': True
                }
                await music_player.queue.put(queue_item)
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{video.get('title', track_name)}]({video_url})",
                    color=0xC7CEEA if is_kawaii else discord.Color.blue()
                )
                if video.get("thumbnail"):
                    embed.set_thumbnail(url=video["thumbnail"])
                if is_kawaii:
                    embed.set_footer(text="☆⌒(≧▽° )")
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            except Exception as e:
                logger.error(f"Error converting Deezer track to YouTube for {query}: {e}")
                embed = Embed(
                    description=get_messages("search_error", guild_id),
                    color=0xFFB6C1 if is_kawaii else discord.Color.red()
                )
                try:
                    await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
                except discord.errors.NotFound:
                    logger.warning(f"Interaction expired for single Deezer track error. Sending public message.")
                    await interaction.channel.send(content=f"{interaction.user.mention}, an error occurred.", embed=embed, silent=SILENT_MESSAGES)
        else:
            embed = Embed(
                title="Deezer playlist processing",
                description="Starting...",
                color=0xFFB6C1 if is_kawaii else discord.Color.blue()
            )
            message = await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)

            total_tracks = len(deezer_tracks)
            processed = 0
            failed = 0
            failed_tracks = []
            batch_size = 50

            logger.info(f"Processing {total_tracks} tracks from Deezer playlist")
            for i in range(0, total_tracks, batch_size):
                batch = deezer_tracks[i:i + batch_size]
                tasks = [search_track(track) for track in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception) or result[1] is None:
                        failed += 1
                        if len(failed_tracks) < 5:
                            # result[2] is track_name, result[3] is artist_name
                            failed_tracks.append(f"{result[2]} by {result[3]}")
                    else:
                        # We get all the info
                        _, video_url, track_name, artist_name = result
                        
                        # We create the object for the queue with a TEMPORARY title
                        queue_item = {
                            'url': video_url,
                            'title': f"{track_name} - {artist_name}", # The temporary title!
                            'webpage_url': video_url,
                            'is_single': False
                        }
                        await music_player.queue.put(queue_item)
                    processed += 1

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

            logger.info(f"Deezer playlist processed: {processed - failed} tracks added, {failed} failed")

            if processed - failed == 0:
                embed = Embed(
                    description="No tracks could be added to the queue.",
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                await message.edit(embed=embed)
                return

            failed_text = "\nFailed tracks (up to 5):\n" + "\n".join([f"- {track}" for track in failed_tracks]) if failed_tracks else ""
            embed.title = get_messages("deezer_playlist_added", guild_id)
            embed.description = get_messages("deezer_playlist_description", guild_id).format(
                count=processed - failed,
                failed=failed,
                failed_tracks=failed_text
            )
            embed.color = 0xB5EAD7 if is_kawaii else discord.Color.green()
            await message.edit(embed=embed)

            if not music_player.hydration_task or music_player.hydration_task.done():
                logger.info(f"[{guild_id}] Spawning background hydration task for the queue.")
                music_player.hydration_task = bot.loop.create_task(background_queue_hydrator(guild_id))

    elif apple_music_regex.match(query):
        apple_tracks = await process_apple_music_url(query, interaction)
        if not apple_tracks:
            return
        if len(apple_tracks) == 1:
            track_name, artist_name = apple_tracks[0]
            query = f"{track_name} {artist_name}"
            try:
                cache_key = sanitize_query(query).lower()
                ydl_opts_full = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "no_color": True,
                    "socket_timeout": 10,
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
                logger.debug(f"Metadata for single Apple Music track: {video}")
                url_cache[cache_key] = video_url
                queue_item = {
                    'url': video_url,
                    'title': video.get('title', track_name),
                    'webpage_url': video_url,
                    'thumbnail': video.get('thumbnail'),
                    'is_single': True,
                    'skip_now_playing': True
                }
                await music_player.queue.put(queue_item)
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{video.get('title', track_name)}]({video_url})",
                    color=0xC7CEEA if is_kawaii else discord.Color.blue()
                )
                if video.get("thumbnail"):
                    embed.set_thumbnail(url=video["thumbnail"])
                if is_kawaii:
                    embed.set_footer(text="☆⌒(≧▽° )")
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            except Exception as e:
                logger.error(f"Apple Music conversion error for {query}: {e}")
                embed = Embed(
                    description=get_messages("search_error", guild_id),
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                try:
                    await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
                except discord.errors.NotFound:
                    logger.warning(f"Interaction expired for single Apple Music track error. Sending public message.")
                    await interaction.channel.send(content=f"{interaction.user.mention}, an error occurred.", embed=embed, silent=SILENT_MESSAGES)
        else:
            embed = Embed(
                title="Apple Music playlist processing",
                description="Starting...",
                color=0xFFB6C1 if is_kawaii else discord.Color.blue()
            )
            message = await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            total_tracks = len(apple_tracks)
            processed = 0
            failed = 0
            failed_tracks = []
            batch_size = 50
            for i in range(0, total_tracks, batch_size):
                batch = apple_tracks[i:i + batch_size]
                tasks = [search_track(track) for track in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception) or result[1] is None:
                        failed += 1
                        if len(failed_tracks) < 5:
                            # result[2] is track_name, result[3] is artist_name
                            failed_tracks.append(f"{result[2]} by {result[3]}")
                    else:
                        # We get all the info
                        _, video_url, track_name, artist_name = result
                        
                        # We create the object for the queue with a TEMPORARY title
                        queue_item = {
                            'url': video_url,
                            'title': f"{track_name} - {artist_name}", # The temporary title!
                            'webpage_url': video_url,
                            'is_single': False
                        }
                        await music_player.queue.put(queue_item)
                    processed += 1
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
            if processed - failed == 0:
                embed = Embed(
                    description="No tracks could be added.",
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                await message.edit(embed=embed)
                return
            failed_text = "\nFailed tracks (up to 5):\n" + "\n".join([f"- {track}" for track in failed_tracks]) if failed_tracks else ""
            embed.title = get_messages("apple_music_playlist_added", guild_id)
            embed.description = get_messages("apple_music_playlist_description", guild_id).format(
                count=processed - failed,
                failed=failed,
                failed_tracks=failed_text
            )
            embed.color = 0xB5EAD7 if is_kawaii else discord.Color.green()
            await message.edit(embed=embed)

            if not music_player.hydration_task or music_player.hydration_task.done():
                logger.info(f"[{guild_id}] Spawning background hydration task for the queue.")
                music_player.hydration_task = bot.loop.create_task(background_queue_hydrator(guild_id))

    elif tidal_regex.match(query):
        tidal_tracks = await process_tidal_url(query, interaction)
        if not tidal_tracks:
            return

        if len(tidal_tracks) == 1:
            track_name, artist_name = tidal_tracks[0]
            query = f"{track_name} {artist_name}"
            try:
                cache_key = sanitize_query(query).lower()
                ydl_opts_full = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "no_color": True,
                    "socket_timeout": 10,
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
                logger.debug(f"Metadata for single Tidal track: {video}")
                url_cache[cache_key] = video_url
                queue_item = {
                    'url': video_url,
                    'title': video.get('title', track_name),
                    'webpage_url': video_url,
                    'thumbnail': video.get('thumbnail'),
                    'is_single': True,
                    'skip_now_playing': True
                }
                await music_player.queue.put(queue_item)
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{video.get('title', track_name)}]({video_url})",
                    color=0xC7CEEA if is_kawaii else discord.Color.blue()
                )
                if video.get("thumbnail"):
                    embed.set_thumbnail(url=video["thumbnail"])
                if is_kawaii:
                    embed.set_footer(text="☆⌒(≧▽° )")
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            except Exception as e:
                logger.error(f"Tidal conversion error for {query}: {e}")
                embed = Embed(
                    description=get_messages("search_error", guild_id),
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                try:
                    await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
                except discord.errors.NotFound:
                    logger.warning(f"Interaction expired for single Tidal track error. Sending public message.")
                    await interaction.channel.send(content=f"{interaction.user.mention}, an error occurred.", embed=embed, silent=SILENT_MESSAGES)
        else:
            embed = Embed(
                title="Tidal mix/playlist processing",
                description="Starting...",
                color=0xFFB6C1 if is_kawaii else discord.Color.blue()
            )
            message = await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            total_tracks = len(tidal_tracks)
            processed = 0
            failed = 0
            failed_tracks = []
            batch_size = 50
            for i in range(0, total_tracks, batch_size):
                batch = tidal_tracks[i:i + batch_size]
                tasks = [search_track(track) for track in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception) or result[1] is None:
                        failed += 1
                        if len(failed_tracks) < 5:
                            # result[2] is track_name, result[3] is artist_name
                            failed_tracks.append(f"{result[2]} by {result[3]}")
                    else:
                        # We get all the info
                        _, video_url, track_name, artist_name = result
                        
                        # We create the object for the queue with a TEMPORARY title
                        queue_item = {
                            'url': video_url,
                            'title': f"{track_name} - {artist_name}", # The temporary title!
                            'webpage_url': video_url,
                            'is_single': False
                        }
                        await music_player.queue.put(queue_item)
                    processed += 1
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
            if processed - failed == 0:
                embed = Embed(
                    description="No tracks could be added.",
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                await message.edit(embed=embed)
                return
            failed_text = "\nFailed tracks (up to 5):\n" + "\n".join([f"- {track}" for track in failed_tracks]) if failed_tracks else ""
            embed.title = get_messages("tidal_playlist_added", guild_id)
            embed.description = get_messages("tidal_playlist_description", guild_id).format(
                count=processed - failed,
                failed=failed,
                failed_tracks=failed_text
            )
            embed.color = 0xB5EAD7 if is_kawaii else discord.Color.green()
            await message.edit(embed=embed)

            if not music_player.hydration_task or music_player.hydration_task.done():
                logger.info(f"[{guild_id}] Spawning background hydration task for the queue.")
                music_player.hydration_task = bot.loop.create_task(background_queue_hydrator(guild_id))

    elif amazon_music_regex.match(query):
        logger.info(f"Attempting to process an Amazon Music URL: {query}")
        amazon_tracks = await process_amazon_music_url(query, interaction)
        if not amazon_tracks:
            logger.error(f"No Amazon Music tracks extracted for {query}")
            return

        if len(amazon_tracks) == 1:
            track_name, artist_name = amazon_tracks[0]
            query = f"{track_name} {artist_name}"
            try:
                cache_key = sanitize_query(query).lower()
                ydl_opts_full = {
                    "format": "bestaudio/best",
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "no_color": True,
                    "socket_timeout": 10,
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
                logger.debug(f"Metadata for single Amazon Music track: {video}")
                url_cache[cache_key] = video_url
                queue_item = {
                    'url': video_url,
                    'title': video.get('title', track_name),
                    'webpage_url': video_url,
                    'thumbnail': video.get('thumbnail'),
                    'is_single': True,
                    'skip_now_playing': True
                }
                await music_player.queue.put(queue_item)
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{video.get('title', track_name)}]({video_url})",
                    color=0xC7CEEA if is_kawaii else discord.Color.blue()
                )
                if video.get("thumbnail"):
                    embed.set_thumbnail(url=video["thumbnail"])
                if is_kawaii:
                    embed.set_footer(text="☆⌒(≧▽° )")
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            except Exception as e:
                logger.error(f"Amazon Music conversion error for {query}: {e}")
                embed = Embed(
                    description=get_messages("search_error", guild_id),
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                try:
                    await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
                except discord.errors.NotFound:
                    logger.warning(f"Interaction expired for single Amazon Music track error. Sending public message.")
                    await interaction.channel.send(content=f"{interaction.user.mention}, an error occurred.", embed=embed, silent=SILENT_MESSAGES)
        else:
            embed = Embed(
                title="Amazon Music playlist processing",
                description="Starting...",
                color=0xFFB6C1 if is_kawaii else discord.Color.blue()
            )
            message = await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
            total_tracks = len(amazon_tracks)
            processed = 0
            failed = 0
            failed_tracks = []
            batch_size = 50
            for i in range(0, total_tracks, batch_size):
                batch = amazon_tracks[i:i + batch_size]
                tasks = [search_track(track) for track in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception) or result[1] is None:
                        failed += 1
                        if len(failed_tracks) < 5:
                            # result[2] is track_name, result[3] is artist_name
                            failed_tracks.append(f"{result[2]} by {result[3]}")
                    else:
                        # We get all the info
                        _, video_url, track_name, artist_name = result
                        
                        # We create the object for the queue with a TEMPORARY title
                        queue_item = {
                            'url': video_url,
                            'title': f"{track_name} - {artist_name}", # The temporary title!
                            'webpage_url': video_url,
                            'is_single': False
                        }
                        await music_player.queue.put(queue_item)
                    processed += 1
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
            if processed - failed == 0:
                embed = Embed(
                    description="No tracks could be added.",
                    color=0xFF9AA2 if is_kawaii else discord.Color.red()
                )
                await message.edit(embed=embed)
                return
            failed_text = "\nFailed tracks (up to 5):\n" + "\n".join([f"- {track}" for track in failed_tracks]) if failed_tracks else ""
            embed.title = get_messages("amazon_music_playlist_added", guild_id)
            embed.description = get_messages("amazon_music_playlist_description", guild_id).format(
                count=processed - failed,
                failed=failed,
                failed_tracks=failed_text
            )
            embed.color = 0xB5EAD7 if is_kawaii else discord.Color.green()
            await message.edit(embed=embed)

            if not music_player.hydration_task or music_player.hydration_task.done():
                logger.info(f"[{guild_id}] Spawning background hydration task for the queue.")
                music_player.hydration_task = bot.loop.create_task(background_queue_hydrator(guild_id))

    elif soundcloud_regex.match(query) or youtube_regex.match(query) or ytmusic_regex.match(query) or bandcamp_regex.match(query):
        try:
            platform = ""
            if soundcloud_regex.match(query): platform = "SoundCloud"
            elif ytmusic_regex.match(query): platform = "YouTube Music"
            elif youtube_regex.match(query): platform = "YouTube"
            elif bandcamp_regex.match(query): platform = "Bandcamp"

            try:
                parsed_url = urlparse(query)
                query_params = parse_qs(parsed_url.query)

                if ('youtube.com' in parsed_url.hostname or 'youtu.be' in parsed_url.hostname) and \
                   parsed_url.path == '/watch' and 'list' in query_params and \
                   not query_params['list'][0].startswith('RD'):
                    
                    playlist_id = query_params['list'][0]
                    new_query = f"https://www.youtube.com/playlist?list={playlist_id}"
                    logger.info(f"Transformed YouTube playlist URL: {new_query}")
                    query = new_query
            except Exception as e:
                logger.warning(f"URL transformation failed, continuing with the original. Error: {e}")

            ydl_opts_playlist = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "noplaylist": False,
                "no_color": True,
                "socket_timeout": 10,
            }
            info = await extract_info_async(ydl_opts_playlist, query)

            if "entries" in info and info["entries"]:
                tracks_to_add = []
                for entry in info["entries"]:
                    if not entry: continue
                    if 'entries' in entry and entry.get('entries'):
                        logger.info(f"Nested playlist found: {entry.get('title', 'Unknown Playlist')}. Adding tracks.")
                        for sub_entry in entry['entries']:
                            if sub_entry: tracks_to_add.append(sub_entry)
                    else:
                        tracks_to_add.append(entry)

                if not tracks_to_add:
                    raise ValueError("No playable tracks found after processing.")

                total_tracks = len(tracks_to_add)
                processed = 0
                failed = 0

                embed = Embed(
                    title=f"Processing {platform} Resource",
                    description=get_messages("loading_playlist", guild_id).format(processed=0, total=total_tracks),
                    color=0xFFB6C1 if is_kawaii else discord.Color.blue()
                )
                message = await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed)

                for track_entry in tracks_to_add:
                    try:
                        video_url = track_entry.get('url')
                        if not video_url:
                            logger.warning(f"Skipping entry without a URL: {track_entry.get('title', 'Unknown')}")
                            failed += 1
                            processed += 1
                            continue

                        queue_item = {
                            'url': video_url,
                            'title': track_entry.get('title', 'Unknown Title'),
                            'webpage_url': track_entry.get('webpage_url', video_url),
                            'thumbnail': track_entry.get('thumbnail'),
                            'is_single': False
                        }
                        await music_player.queue.put(queue_item)
                        processed += 1

                        if processed % 10 == 0 or processed == total_tracks:
                            progress = processed / total_tracks
                            bar = create_loading_bar(progress)
                            new_description = f"{bar}\n" + get_messages("loading_playlist", guild_id).format(
                                processed=processed,
                                total=total_tracks
                            )
                            embed.description = new_description
                            await message.edit(embed=embed)
                            await asyncio.sleep(0.1)

                    except Exception as e:
                        logger.error(f"Failed to process a playlist entry: {track_entry.get('title', 'N/A')}. Error: {e}")
                        failed += 1
                        processed += 1
                        continue

                final_added_count = total_tracks - failed
                first_entry_thumbnail = tracks_to_add[0].get("thumbnail") if tracks_to_add else None
                
                title_key = "ytmusic_playlist_added" if ytmusic_regex.match(query) else "playlist_added"
                desc_key = "playlist_description"

                embed.title = get_messages(title_key, guild_id)
                embed.description = get_messages(desc_key, guild_id).format(count=final_added_count)
                
                if failed > 0:
                    embed.description += f"\n({failed} track(s) could not be added.)"

                embed.color = 0xE2F0CB if is_kawaii else discord.Color.green()
                if first_entry_thumbnail:
                    embed.set_thumbnail(url=first_entry_thumbnail)
                await message.edit(embed=embed)

            else:
                queue_item = {
                    'url': info["webpage_url"],
                    'title': info.get('title', 'Unknown Title'),
                    'webpage_url': info["webpage_url"],
                    'thumbnail': info.get('thumbnail'),
                    'is_single': True,
                    'skip_now_playing': True
                }

                await music_player.queue.put(queue_item)
                embed = Embed(
                    title=get_messages("song_added", guild_id),
                    description=f"[{info['title']}]({info['webpage_url']})",
                    color=0xFFDAC1 if is_kawaii else discord.Color.blue()
                )
                if info.get("thumbnail"):
                    embed.set_thumbnail(url=info["thumbnail"])
                await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)
                                
        except yt_dlp.utils.DownloadError as e:
            emoji, title_key, desc_key = parse_yt_dlp_error(str(e))
            
            embed = Embed(
                title=f'{emoji} {get_messages(title_key, guild_id)}',
                description=get_messages(desc_key, guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.orange()
            )
            
            github_url = "https://github.com/alan7383/playify/issues"
            embed.add_field(
                name=f'🤔 {get_messages("error_field_what_to_do", guild_id)}',
                value=get_messages("error_what_to_do_content", guild_id).format(github_link=github_url),
                inline=False
            )

            embed.add_field(
                name=f'📋 {get_messages("error_field_full_error", guild_id)}',
                value=f"```\n{str(e)}\n```",
                inline=False
            )
            
            await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
            logger.warning(f"A user-facing download error occurred: {str(e).splitlines()[0]}")

        except TypeError as e:
            if "'NoneType' object is not subscriptable" in str(e):
                logger.warning(f"Caught a TypeError from yt-dlp, likely an empty/private/unsupported playlist: {query}. Error: {e}")
                embed = Embed(
                    description=get_messages("playlist_error", guild_id),
                    color=0xFF9AA2 if is_kawaii else discord.Color.orange()
                )
                await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
            else:
                logger.error(f"An unexpected TypeError occurred: {e}", exc_info=True)
                raise e
        
        except Exception as e:
            embed = Embed(
                description=get_messages("video_error", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            logger.error(f"Error processing generic URL/Playlist: {e}", exc_info=True)
            try:
                await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
            except discord.errors.NotFound:
                logger.warning(f"Interaction expired for generic URL error. Sending public message.")
                await interaction.channel.send(content=f"{interaction.user.mention}, an error occurred.", embed=embed, silent=SILENT_MESSAGES)

    else:
        try:
            ydl_opts_full = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "no_color": True,
                "socket_timeout": 10,
            }
            
            video_info = {}
            if direct_link_regex.match(query):
                logger.info(f"Direct link detected: {query}")
                search_query = query
                try:
                    parsed_path = urlparse(query).path
                    fallback_title = os.path.basename(parsed_path)
                except:
                    fallback_title = "Fichier audio externe"
                
                info = await extract_info_async(ydl_opts_full, search_query)
                video_info = info
                if not video_info.get('title'):
                    video_info['title'] = fallback_title

            else:
                logger.info(f"Keyword search detected: {query}")
                sanitized_query = sanitize_query(query)
                search_query = f"ytsearch:{sanitized_query}"
                info = await extract_info_async(ydl_opts_full, search_query)
                video_info = info["entries"][0] if "entries" in info and info["entries"] else None

            if not video_info:
                raise Exception("No results found")

            video_url = video_info.get("webpage_url", video_info.get("url"))
            if not video_url:
                raise KeyError("No valid URL found in video metadata")

            logger.debug(f"Metadata for resolved query: {video_info}")
            queue_item = {
                'url': video_url,
                'title': video_info.get('title', 'Unknown Title'),
                'webpage_url': video_url,
                'thumbnail': video_info.get('thumbnail'),
                'is_single': True,
                'skip_now_playing': True
            }

            await music_player.queue.put(queue_item)
            embed = Embed(
                title=get_messages("song_added", guild_id),
                description=f"[{video_info.get('title', 'Unknown Title')}]({video_url})",
                color=0xB5EAD7 if is_kawaii else discord.Color.blue()
            )
            if video_info.get("thumbnail"):
                embed.set_thumbnail(url=video_info["thumbnail"])
            if is_kawaii:
                embed.set_footer(text="☆⌒(≧▽° )")
            await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)

            if not music_player.voice_client.is_playing() and not music_player.voice_client.is_paused():
                music_player.suppress_next_now_playing = True

        except yt_dlp.utils.DownloadError as e:
            emoji, title_key, desc_key = parse_yt_dlp_error(str(e))
            
            embed = Embed(
                title=f'{emoji} {get_messages(title_key, guild_id)}',
                description=get_messages(desc_key, guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.orange()
            )
            
            github_url = "https://github.com/alan7383/playify/issues"
            embed.add_field(
                name=f'🤔 {get_messages("error_field_what_to_do", guild_id)}',
                value=get_messages("error_what_to_do_content", guild_id).format(github_link=github_url),
                inline=False
            )

            embed.add_field(
                name=f'📋 {get_messages("error_field_full_error", guild_id)}',
                value=f"```\n{str(e)}\n```",
                inline=False
            )
            
            await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
            logger.warning(f"A user-facing download error occurred: {str(e).splitlines()[0]}")
        except Exception as e:
            embed = Embed(
                description=get_messages("search_error", guild_id),
                color=0xFF9AA2 if is_kawaii else discord.Color.red()
            )
            logger.error(f"Error searching for {query}: {e}")
            try:
                await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
            except discord.errors.NotFound:
                logger.warning(f"Interaction expired for keyword search error. Sending public message.")
                await interaction.channel.send(content=f"{interaction.user.mention}, an error occurred.", embed=embed, silent=SILENT_MESSAGES)

    if not music_player.voice_client.is_playing() and not music_player.voice_client.is_paused():
        music_player.current_task = asyncio.create_task(play_audio(guild_id))

@bot.tree.command(name="play-files", description="Plays one or more uploaded audio or video files.")
@app_commands.describe(
    file1="The first audio/video file to play.",
    file2="An optional audio/video file.",
    file3="An optional audio/video file.",
    file4="An optional audio/video file.",
    file5="An optional audio/video file.",
    file6="An optional audio/video file.",
    file7="An optional audio/video file.",
    file8="An optional audio/video file.",
    file9="An optional audio/video file.",
    file10="An optional audio/video file."
)
async def play_files(
    interaction: discord.Interaction, 
    file1: discord.Attachment,
    file2: discord.Attachment = None, file3: discord.Attachment = None,
    file4: discord.Attachment = None, file5: discord.Attachment = None,
    file6: discord.Attachment = None, file7: discord.Attachment = None,
    file8: discord.Attachment = None, file9: discord.Attachment = None,
    file10: discord.Attachment = None
):
    """
    Downloads, saves, and queues one or more user-uploaded audio/video files.
    """

    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    await interaction.response.defer()

    voice_client = await ensure_voice_connection(interaction)
    if not voice_client:
        return
    
    base_cache_dir = "audio_cache"
    guild_cache_dir = os.path.join(base_cache_dir, str(guild_id))
    os.makedirs(guild_cache_dir, exist_ok=True)
    
    attachments = [f for f in [file1, file2, file3, file4, file5, file6, file7, file8, file9, file10] if f is not None]
    
    added_files = []
    failed_files = []

    for attachment in attachments:
        if not attachment.content_type or not (attachment.content_type.startswith("audio/") or attachment.content_type.startswith("video/")):
            failed_files.append(attachment.filename)
            continue
            
        file_path = os.path.join(guild_cache_dir, attachment.filename)
        try:
            await attachment.save(file_path)
            logger.info(f"File saved for guild {guild_id}: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file {attachment.filename}: {e}")
            failed_files.append(attachment.filename)
            continue

        queue_item = {
            'url': file_path,
            'title': attachment.filename,
            'webpage_url': None,
            'thumbnail': None,
            'is_single': True,
            # 'skip_now_playing': True,  <- This line is removed
            'source_type': 'file'
        }
        await music_player.queue.put(queue_item)
        added_files.append(attachment.filename)

        # If 24/7 mode is active, also add the file to the permanent radio playlist
        if _24_7_active.get(guild_id, False):
            music_player.radio_playlist.append(queue_item)
            logger.info(f"Added '{attachment.filename}' to the active 24/7 radio playlist for guild {guild_id}.")

    if not added_files:
        await interaction.followup.send(embed=Embed(description="No valid audio/video files were added.", color=0xFF9AA2 if is_kawaii else discord.Color.red()), ephemeral=True, silent=SILENT_MESSAGES)
        return

    description = f"**{len(added_files)} file(s) added to the queue:**\n" + "\n".join([f"• `{name}`" for name in added_files[:10]])
    if len(added_files) > 10:
        description += f"\n... and {len(added_files) - 10} more."
    if failed_files:
        description += f"\n\n**{len(failed_files)} file(s) ignored (invalid type).**"

    embed = Embed(title="Files Added to Queue", description=description, color=0xB5EAD7 if is_kawaii else discord.Color.blue())
    await interaction.followup.send(embed=embed, silent=SILENT_MESSAGES)

    if not music_player.voice_client.is_playing() and not music_player.voice_client.is_paused():
        music_player.current_task = asyncio.create_task(play_audio(guild_id))

# /queue command
@bot.tree.command(name="queue", description="Show the current song queue and status with pages.")
async def queue(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    await interaction.response.defer()
    guild_id = interaction.guild_id
    music_player = get_player(guild_id)

    # We work on a copy of the list to avoid interfering with the player
    all_tracks = list(music_player.queue._queue)

    if not all_tracks and not music_player.current_info:
        is_kawaii = get_mode(guild_id)
        embed = Embed(
            description=get_messages("queue_empty", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
        return

    # The view will now handle the hydration and pagination itself
    view = QueueView(interaction=interaction, tracks=all_tracks, items_per_page=5)
    view.update_button_states()
    initial_embed = await view.create_queue_embed()
    await interaction.followup.send(embed=initial_embed, view=view, silent=SILENT_MESSAGES)

@bot.tree.command(name="clearqueue", description="Clear the current queue")
async def clear_queue(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    while not music_player.queue.empty():
        music_player.queue.get_nowait()

    music_player.history.clear()
    music_player.radio_playlist.clear()

    # --- LINE REMOVED ---
    # clear_audio_cache(guild_id) # We no longer clear the cache here

    embed = Embed(description=get_messages("clear_queue_success", guild_id), color=0xB5EAD7 if is_kawaii else discord.Color.green())
    await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed)

@bot.tree.command(name="playnext", description="Add a song or a local file to play next")
@app_commands.describe(
    query="Link or title of the video/song to play next.",
    file="The local audio/video file to play next."
)
async def play_next(interaction: discord.Interaction, query: str = None, file: discord.Attachment = None):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    if (query and file) or (not query and not file):
        embed = Embed(
            description="Please provide either a link/search term OR a file, but not both.",
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        return

    await interaction.response.defer()
    
    voice_client = await ensure_voice_connection(interaction)
    if not voice_client:
        return

    queue_item = None

    # --- BRANCHE 1 : L'utilisateur a fourni un lien ou une recherche ---
    if query:
        # On définit la regex ici aussi pour la détection
        direct_link_regex = re.compile(r'^(https?://).+\.(mp3|wav|ogg|m4a|mp4|webm|flac)(\?.+)?$', re.IGNORECASE)
        try:
            info = {}
            # --- NOUVELLE LOGIQUE DE DÉTECTION ---
            # Cas A : C'est un lien direct vers un fichier
            if direct_link_regex.match(query):
                logger.info(f"/playnext detected a direct link: {query}")
                ydl_opts = {"format": "bestaudio/best", "quiet": True, "no_warnings": True, "noplaylist": True}
                info = await extract_info_async(ydl_opts, query)
                if not info.get('title'):
                    info['title'] = os.path.basename(urlparse(query).path)

            # Cas B : C'est un lien de plateforme (Spotify, Deezer...)
            else:
                spotify_regex = re.compile(r'^(https?://)?(open\.spotify\.com)/.+$')
                deezer_regex = re.compile(r'^(https?://)?((www\.)?deezer\.com/(?:[a-z]{2}/)?(track|playlist|album|artist)/.+|(link\.deezer\.com)/s/.+)$')
                apple_music_regex = re.compile(r'^(https?://)?(music\.apple\.com)/.+$')
                tidal_regex = re.compile(r'^(https?://)?(www\.)?tidal\.com/.+$')
                amazon_music_regex = re.compile(r'^(https?://)?(music\.amazon\.(fr|com|co\.uk|de|es|it|jp))/.+$')

                tracks = None
                if spotify_regex.match(query): tracks = await process_spotify_url(query, interaction)
                elif deezer_regex.match(query): tracks = await process_deezer_url(query, interaction)
                elif apple_music_regex.match(query): tracks = await process_apple_music_url(query, interaction)
                elif tidal_regex.match(query): tracks = await process_tidal_url(query, interaction)
                elif amazon_music_regex.match(query): tracks = await process_amazon_music_url(query, interaction)

                search_query_for_yt = query
                if tracks:
                    if len(tracks) > 1:
                        raise Exception("Playlists and albums are not supported for /playnext.")
                    track_name, artist_name = tracks[0]
                    search_query_for_yt = f"{track_name} {artist_name}"

                ydl_opts = {"format": "bestaudio/best", "quiet": True, "no_warnings": True, "noplaylist": True}
                yt_search_term = f"ytsearch:{sanitize_query(search_query_for_yt)}" if not search_query_for_yt.startswith(('http://', 'https://')) else search_query_for_yt
                search_results = await extract_info_async(ydl_opts, yt_search_term)
                info = search_results["entries"][0] if "entries" in search_results and search_results["entries"] else search_results

            # --- FIN DE LA NOUVELLE LOGIQUE ---

            if not info:
                raise Exception("Could not find any video or track information.")

            queue_item = {
                'url': info.get("webpage_url", info.get("url")),
                'title': info.get('title', 'Unknown Title'),
                'webpage_url': info.get("webpage_url", info.get("url")),
                'thumbnail': info.get('thumbnail'),
                'is_single': True
            }

        except Exception as e:
            embed = Embed(description=get_messages("search_error", guild_id), color=0xFF9AA2 if is_kawaii else discord.Color.red())
            await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
            logger.error(f"Error processing /playnext for query '{query}': {e}", exc_info=True)
            return
            
    # --- BRANCHE 2 : L'utilisateur a fourni un fichier local (inchangée) ---
    elif file:
        try:
            if not file.content_type or not (file.content_type.startswith("audio/") or file.content_type.startswith("video/")):
                embed = Embed(description="Invalid file type. Please upload an audio or video file.", color=0xFF9AA2 if is_kawaii else discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
                return

            guild_cache_dir = os.path.join("audio_cache", str(guild_id))
            os.makedirs(guild_cache_dir, exist_ok=True)
            file_path = os.path.join(guild_cache_dir, file.filename)
            await file.save(file_path)
            logger.info(f"File saved for /playnext in guild {guild_id}: {file_path}")

            queue_item = {
                'url': file_path,
                'title': file.filename,
                'webpage_url': None,
                'thumbnail': None,
                'is_single': True,
                'source_type': 'file'
            }
        except Exception as e:
            embed = Embed(description="An error occurred while processing the file.", color=0xFF9AA2 if is_kawaii else discord.Color.red())
            await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)
            logger.error(f"Error processing file in /playnext for guild {guild_id}: {e}")
            return

    # --- LOGIQUE COMMUNE : Ajout à la file et confirmation (inchangée) ---
    if queue_item:
        new_queue = asyncio.Queue()
        await new_queue.put(queue_item)
        while not music_player.queue.empty():
            item = await music_player.queue.get()
            await new_queue.put(item)
        music_player.queue = new_queue

        description_text = ""
        if queue_item.get('source_type') == 'file':
            description_text = f"💿 `{queue_item['title']}`"
        else:
            description_text = f"[{queue_item['title']}]({queue_item['webpage_url']})"

        embed = Embed(
            title=get_messages("play_next_added", guild_id),
            description=description_text,
            color=0xC7CEEA if is_kawaii else discord.Color.blue()
        )
        if queue_item.get("thumbnail"):
            embed.set_thumbnail(url=queue_item["thumbnail"])
        if is_kawaii:
            embed.set_footer(text="☆⌒(≧▽° )")
        await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed)

        if not music_player.voice_client.is_playing() and not music_player.voice_client.is_paused():
            music_player.current_task = asyncio.create_task(play_audio(guild_id))

@bot.tree.command(name="nowplaying", description="Show the current song playing")
async def now_playing(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    if music_player.current_info:
        title = music_player.current_info.get("title", "Unknown Title")
        thumbnail = music_player.current_info.get("thumbnail")
        
        description_text = ""
        if music_player.current_info.get('source_type') == 'file':
            description_text = f"💿 `{title}`"
        else:
            url = music_player.current_info.get("webpage_url", music_player.current_url)
            description_text = get_messages("now_playing_description", guild_id).format(title=title, url=url)

        embed = Embed(
            title=get_messages("now_playing_title", guild_id),
            description=description_text,
            color=0xC7CEEA if is_kawaii else discord.Color.green()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        await interaction.response.send_message(silent=SILENT_MESSAGES, embed=embed)
    else:
        embed = Embed(
            description=get_messages("no_song_playing", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(silent=SILENT_MESSAGES, embed=embed, ephemeral=True)

@bot.tree.command(name="filter", description="Applies or removes audio filters in real time.")
async def filter_command(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild.id
    music_player = get_player(guild_id)
    is_kawaii = get_mode(guild_id)

    if not music_player.voice_client or not (music_player.voice_client.is_playing() or music_player.voice_client.is_paused()):
        embed = Embed(
            description=get_messages("no_filter_playback", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)
        return

    # Creates and sends the view with the buttons
    view = FilterView(interaction)
    embed = Embed(
        title=get_messages("filter_title", guild_id),
        description=get_messages("filter_description", guild_id),
        color=0xB5EAD7 if is_kawaii else discord.Color.blue()
    )

    # KEY CHANGE: "ephemeral=True" is removed to make the message public
    await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, view=view)

# /pause command
@bot.tree.command(name="pause", description="Pause the current playback")
async def pause(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    voice_client = await ensure_voice_connection(interaction)

    if voice_client and voice_client.is_playing():
        # --- TIMER MANAGEMENT ---
        if music_player.playback_started_at:
            elapsed_since_play = time.time() - music_player.playback_started_at
            music_player.start_time += elapsed_since_play * music_player.playback_speed
            music_player.playback_started_at = None
        # --- END TIMER MANAGEMENT ---
            
        voice_client.pause()
        embed = Embed(
            description=get_messages("pause", guild_id),
            color=0xFFB7B2 if is_kawaii else discord.Color.orange()
        )
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed)
    else:
        embed = Embed(
            description=get_messages("no_playback", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)

# /resume command
@bot.tree.command(name="resume", description="Resume the playback")
async def resume(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    voice_client = await ensure_voice_connection(interaction)

    if voice_client and voice_client.is_paused():
        # --- TIMER MANAGEMENT ---
        if music_player.playback_started_at is None:
            music_player.playback_started_at = time.time()
        # --- END TIMER MANAGEMENT ---

        voice_client.resume()
        embed = Embed(
            description=get_messages("resume", guild_id),
            color=0xB5EAD7 if is_kawaii else discord.Color.green()
        )
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed)
    else:
        embed = Embed(
            description=get_messages("no_paused", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)

# /skip command
@bot.tree.command(name="skip", description="Skip to the next song")
async def skip(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    voice_client = await ensure_voice_connection(interaction)

    if not voice_client or not voice_client.is_playing():
        embed = Embed(
            description=get_messages("no_song", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        return

    if music_player.lyrics_task and not music_player.lyrics_task.done():
        music_player.lyrics_task.cancel()

    if not interaction.response.is_done():
        await interaction.response.defer()

    # --- Replay Logic for when loop is enabled ---
    if music_player.loop_current:
        title = music_player.current_info.get("title", "Unknown Title")
        thumbnail = music_player.current_info.get("thumbnail")
        
        description_text = ""
        if music_player.current_info.get('source_type') == 'file':
            formatted_song = f"💿 `{title}`"
            if is_kawaii:
                description_text = f"Let's listen to {formatted_song} one more time!~ (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
            else:
                description_text = f"Restarting {formatted_song} from the beginning."
        else:
            url = music_player.current_info.get("webpage_url", music_player.current_url)
            description_text = get_messages("replay_success_desc", guild_id).format(title=title, url=url)

        embed = Embed(
            title=get_messages("replay_success_title", guild_id),
            description=description_text,
            color=0xC7CEEA if is_kawaii else discord.Color.blue()
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed)
        voice_client.stop()

    # --- Standard Skip Logic ---
    else:
        queue_snapshot = list(music_player.queue._queue)
        
        if not queue_snapshot:
            embed = Embed(
                description=get_messages("skip_confirmation", guild_id) + "\n*" + get_messages("skip_queue_empty", guild_id) + "*",
                color=0xE2F0CB if is_kawaii else discord.Color.blue()
            )
            await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed)
        else:
            next_song_info = queue_snapshot[0]
            
            if not next_song_info.get('thumbnail') and not next_song_info.get('source_type') == 'file':
                try:
                    full_info = await extract_info_async({"format": "bestaudio/best", "quiet": True}, next_song_info['url'])
                    next_song_info['title'] = full_info.get('title', 'Unknown Title')
                    next_song_info['thumbnail'] = full_info.get('thumbnail')
                except Exception as e:
                    logger.error(f"Failed to hydrate track during skip: {e}")

            title = next_song_info.get("title", "Unknown Title")
            thumbnail = next_song_info.get("thumbnail")
            
            description_text = ""
            if next_song_info.get('source_type') == 'file':
                description_text = f"💿 `{title}`"
            else:
                url = next_song_info.get("webpage_url", next_song_info.get("url", "#"))
                description_text = f"[{title}]({url})"

            embed = Embed(
                title=get_messages("now_playing_title", guild_id),
                description=description_text,
                color=0xC7CEEA if is_kawaii else discord.Color.green()
            )
            embed.set_author(name=get_messages("skip_confirmation", guild_id))
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)

            await interaction.followup.send(silent=SILENT_MESSAGES, embed=embed)
        
        music_player.suppress_next_now_playing = True
        voice_client.stop() 

# /loop command
@bot.tree.command(name="loop", description="Enable/disable looping")
async def loop(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    # 1. Defer the interaction immediately
    await interaction.response.defer()

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    music_player.loop_current = not music_player.loop_current
    state = get_messages("loop_state_enabled", guild_id) if music_player.loop_current else get_messages("loop_state_disabled", guild_id)

    embed = Embed(
        description=get_messages("loop", guild_id).format(state=state),
        color=0xC7CEEA if is_kawaii else discord.Color.blue()
    )
    
    # 2. Send the actual response as a follow-up
    await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)

# /stop command
@bot.tree.command(name="stop", description="Stop playback and disconnect the bot")
async def stop(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    if music_player.lyrics_task and not music_player.lyrics_task.done():
        music_player.lyrics_task.cancel()

    if music_player.voice_client:
        if music_player.current_task and not music_player.current_task.done():
            music_player.current_task.cancel()

        if music_player.voice_client.is_playing():
            music_player.voice_client.stop()

        await music_player.voice_client.disconnect()

        # --- LINE ADDED ---
        clear_audio_cache(guild_id) # Clean up saved files

        music_players[guild_id] = MusicPlayer()

        embed = Embed(description=get_messages("stop", guild_id), color=0xFF9AA2 if is_kawaii else discord.Color.red())
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed)
    else:
        embed = Embed(description=get_messages("not_connected", guild_id), color=0xFF9AA2 if is_kawaii else discord.Color.red())
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)

# /shuffle command
@bot.tree.command(name="shuffle", description="Shuffle the current queue")
async def shuffle(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

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
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed)
    else:
        embed = Embed(
            description=get_messages("queue_empty", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, ephemeral=True)

# /autoplay command
@bot.tree.command(name="autoplay", description="Enable/disable autoplay of similar songs")
async def toggle_autoplay(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    music_player.autoplay_enabled = not music_player.autoplay_enabled
    state = get_messages("autoplay_state_enabled", guild_id) if music_player.autoplay_enabled else get_messages("autoplay_state_disabled", guild_id)

    embed = Embed(
        description=get_messages("autoplay_toggle", guild_id).format(state=state),
        color=0xC7CEEA if is_kawaii else discord.Color.blue()
    )
    await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed)

# /status command (hyper-complete version)
@bot.tree.command(name="status", description="Displays the bot's full performance and diagnostic stats.")
async def status(interaction: discord.Interaction):

    # --- Helper function to format bytes ---
    def format_bytes(size):
        if size == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return f"{s} {size_name[i]}"

    await interaction.response.defer(ephemeral=True) # Defer for a potentially long operation

    # === BOT & DISCORD METRICS ===
    bot_process = psutil.Process()
    latency = round(bot.latency * 1000)
    server_count = len(bot.guilds)
    user_count = sum(guild.member_count for guild in bot.guilds)
    current_time = time.time()
    uptime_seconds = int(round(current_time - bot.start_time))
    uptime_string = str(datetime.timedelta(seconds=uptime_seconds))

    # === MUSIC & PLAYER METRICS ===
    active_players = len(music_players)
    total_queued_songs = sum(p.queue.qsize() for p in music_players.values())

    # Count active FFmpeg child processes
    ffmpeg_processes = 0
    try:
        children = bot_process.children(recursive=True)
        for child in children:
            if child.name().lower() == 'ffmpeg':
                ffmpeg_processes += 1
    except psutil.Error:
        ffmpeg_processes = "N/A" # In case of permission errors

    # === HOST SYSTEM METRICS ===
    # CPU
    cpu_freq = psutil.cpu_freq()
    cpu_load = psutil.cpu_percent(interval=0.1) # 0.1s interval for a quick check

    # Memory
    ram_info = psutil.virtual_memory()
    ram_total = format_bytes(ram_info.total)
    ram_used = format_bytes(ram_info.used)
    ram_percent = ram_info.percent
    bot_ram_usage = format_bytes(bot_process.memory_info().rss)

    # Disk
    disk_info = psutil.disk_usage('/')
    disk_total = format_bytes(disk_info.total)
    disk_used = format_bytes(disk_info.used)
    disk_percent = disk_info.percent

    # === ENVIRONMENT & LIBRARIES ===
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    discord_py_version = discord.__version__
    yt_dlp_version = yt_dlp.version.__version__
    os_info = f"{platform.system()} {platform.release()}"

    # === ASSEMBLE THE EMBED ===
    embed = discord.Embed(
        title=f"Playify's Dashboard",
        description=f"Full operational status of the bot and its environment.",
        color=0x2ECC71 if latency < 200 else (0xE67E22 if latency < 500 else 0xE74C3C) # Color changes with latency
    )
    embed.set_thumbnail(url=bot.user.avatar.url)

    embed.add_field(
        name="📊 Bot",
        value=f"**Discord Latency:** {latency} ms\n"
              f"**Servers:** {server_count}\n"
              f"**Users:** {user_count}\n"
              f"**Uptime:** {uptime_string}",
        inline=True
    )

    embed.add_field(
        name="🎧 Music Player",
        value=f"**Active Players:** {active_players}\n"
              f"**Queued Songs:** {total_queued_songs}\n"
              f"**FFmpeg Processes:** `{ffmpeg_processes}`\n"
              f"**URL Cache:** {url_cache.currsize}/{url_cache.maxsize}",
        inline=True
    )

    embed.add_field(name="\u200b", value="\u200b", inline=False) # Spacer

    embed.add_field(
        name="💻 Host System",
        value=f"**OS:** {os_info}\n"
              f"**CPU:** {cpu_load}% @ {cpu_freq.current:.0f}MHz\n"
              f"**RAM:** {ram_used} / {ram_total} ({ram_percent}%)\n"
              f"**Disk:** {disk_used} / {disk_total} ({disk_percent}%)",
        inline=True
    )

    embed.add_field(
        name="⚙️ Environment",
        value=f"**Python:** v{python_version}\n"
              f"**Discord.py:** v{discord_py_version}\n"
              f"**yt-dlp:** v{yt_dlp_version}\n"
              f"**Bot RAM Usage:** {bot_ram_usage}",
        inline=True
    )

    embed.set_footer(text=f"Data requested by {interaction.user.display_name}")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

    await interaction.followup.send(silent=SILENT_MESSAGES,embed=embed)

# /discord command
@bot.tree.command(name="discord", description="Get an invite to the official community and support server.")
async def discord_command(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    
    # Create the embed using messages from the dictionary
    embed = Embed(
        title=get_messages("discord_command_title", guild_id),
        description=get_messages("discord_command_description", guild_id),
        color=0xFFB6C1 if is_kawaii else discord.Color.blue()
    )
    
    # Create a View to hold the button
    view = View()
    
    # Create a button that links to your server
    button = Button(
        label=get_messages("discord_command_button", guild_id),
        style=discord.ButtonStyle.link,
        url="https://discord.gg/JeH8g6g3cG" # Your server invite link
    )
    
    # Add the button to the view
    view.add_item(button)
    
    # Send the response with the embed and button
    await interaction.response.send_message(silent=SILENT_MESSAGES,embed=embed, view=view)    

@bot.tree.command(name="24_7", description="Enable or disable 24/7 mode.")
@app_commands.describe(mode="Choose the mode: auto (adds songs), normal (loops the queue), or off.")
@app_commands.choices(mode=[
    Choice(name="Normal (Loops the current queue)", value="normal"),
    Choice(name="Auto (Adds similar songs when the queue is empty)", value="auto"),
    Choice(name="Off (Disable 24/7 mode)", value="off")
])
async def radio_24_7(interaction: discord.Interaction, mode: str):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    await interaction.response.defer(thinking=True)

    # Case 1: The user wants to disable 24/7 mode
    if mode == "off":
        if not _24_7_active.get(guild_id, False):
            await interaction.followup.send("24/7 mode was not active.", silent=SILENT_MESSAGES, ephemeral=True)
            return

        _24_7_active[guild_id] = False
        music_player.autoplay_enabled = False
        music_player.loop_current = False
        music_player.radio_playlist.clear()
                
        embed = Embed(
            title=get_messages("24_7_off_title", guild_id),
            description=get_messages("24_7_off_desc", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.followup.send(embed=embed, silent=SILENT_MESSAGES)
        return

    voice_client = await ensure_voice_connection(interaction)
    if not voice_client:
        if music_player.text_channel:
             await music_player.text_channel.send("Unable to connect to the voice chat.", silent=SILENT_MESSAGES)
        return

    if not music_player.radio_playlist:
        logger.info(f"[{guild_id}] 24/7 mode enabled. Creating radio playlist snapshot.")
        if music_player.current_info:
             music_player.radio_playlist.append({
                 'url': music_player.current_url, 
                 'title': music_player.current_info.get('title', 'Unknown Title'), 
                 'webpage_url': music_player.current_info.get('webpage_url', music_player.current_url), 
                 'is_single': False,
                 'source_type': music_player.current_info.get('source_type')
            })
        
        queue_snapshot = list(music_player.queue._queue)
        music_player.radio_playlist.extend(queue_snapshot)

    if not music_player.radio_playlist and mode == "normal":
        await interaction.followup.send("The queue is empty. Add songs before enabling 24/7 normal mode.", silent=SILENT_MESSAGES, ephemeral=True)
        return

    _24_7_active[guild_id] = True
    music_player.loop_current = False

    if mode == "auto":
        music_player.autoplay_enabled = True
        embed = Embed(
            title=get_messages("24_7_auto_title", guild_id),
            description=get_messages("24_7_auto_desc", guild_id),
            color=0xB5EAD7 if is_kawaii else discord.Color.green()
        )
    else: # mode == "normal"
        music_player.autoplay_enabled = False
        embed = Embed(
            title=get_messages("24_7_normal_title", guild_id),
            description=get_messages("24_7_normal_desc", guild_id),
            color=0xB5EAD7 if is_kawaii else discord.Color.green()
        )
    
    if not music_player.voice_client.is_playing() and not music_player.voice_client.is_paused():
        music_player.current_task = asyncio.create_task(play_audio(guild_id))

    await interaction.followup.send(embed=embed, silent=SILENT_MESSAGES)

@bot.tree.command(name="reconnect", description="Refreshes the voice connection to reduce lag without losing the queue.")
async def reconnect(interaction: discord.Interaction):
    """
    Disconnects and reconnects the bot to the voice channel,
    resuming playback at the precise timestamp.
    """
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    if not music_player.voice_client or not music_player.voice_client.is_connected():
        embed = Embed(
            description=get_messages("not_connected", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        return

    if not music_player.voice_client.is_playing() or not music_player.current_info:
        embed = Embed(
            description=get_messages("reconnect_not_playing", guild_id),
            color=0xFF9AA2 if is_kawaii else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        return

    await interaction.response.defer()

    current_voice_channel = music_player.voice_client.channel
    current_timestamp = 0
    if music_player.playback_started_at:
        real_elapsed_time = time.time() - music_player.playback_started_at
        current_timestamp = music_player.start_time + (real_elapsed_time * music_player.playback_speed)
    
    logger.info(f"[{guild_id}] Reconnect: Storing timestamp at {current_timestamp:.2f}s.")

    try:
        music_player.is_reconnecting = True

        if music_player.voice_client.is_playing():
            music_player.voice_client.stop()
        
        await music_player.voice_client.disconnect(force=True)
        await asyncio.sleep(0.75)
        new_vc = await current_voice_channel.connect()
        music_player.voice_client = new_vc
        
        # --- START OF FIX ---
        # If we reconnected to a Stage Channel, we must promote ourselves to speaker.
        if isinstance(current_voice_channel, discord.StageChannel):
            logger.info(f"[{guild_id}] Reconnected to a Stage Channel. Promoting to speaker.")
            try:
                # Wait a moment for the bot's voice state to be fully available
                await asyncio.sleep(0.5) 
                await interaction.guild.me.edit(suppress=False)
            except Exception as e:
                logger.error(f"[{guild_id}] Failed to promote to speaker after reconnect: {e}")
        # --- END OF FIX ---

        logger.info(f"[{guild_id}] Reconnect: Restarting playback.")
        music_player.current_task = bot.loop.create_task(play_audio(guild_id, seek_time=current_timestamp))
        
        embed = Embed(
            description=get_messages("reconnect_success", guild_id),
            color=0xB5EAD7 if is_kawaii else discord.Color.green()
        )
        await interaction.followup.send(embed=embed, silent=SILENT_MESSAGES)

    except Exception as e:
        logger.error(f"An error occurred during reconnect for guild {guild_id}: {e}", exc_info=True)
        await interaction.followup.send("An error occurred during the reconnect process.", silent=SILENT_MESSAGES, ephemeral=True)
    finally:
        music_player.is_reconnecting = False
        logger.info(f"[{guild_id}] Reconnect: Process finished, flag reset.")
        
# This is the autocomplete function. It's called by Discord as the user types.
async def song_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guild_id = interaction.guild.id
    music_player = get_player(guild_id)
    choices = []
    
    # Get a snapshot of the queue to work with
    tracks = list(music_player.queue._queue)

    # Iterate through the queue and create a choice for each song
    for i, track in enumerate(tracks):
        # We only show up to 25 choices, which is Discord's limit
        if i >= 25:
            break
            
        title = track.get('title', 'Unknown Title')
        
        # The 'name' is what the user sees, the 'value' is what the bot receives
        # We use the index (1-based) as the value for easy removal later.
        choice_name = f"{i + 1}. {title}"
        
        # Filter choices based on what the user is typing
        if current.lower() in choice_name.lower():
            choices.append(app_commands.Choice(name=choice_name[:100], value=str(i + 1)))
            
    return choices

@bot.tree.command(name="remove", description="Opens an interactive menu to remove songs from the queue.")
async def remove(interaction: discord.Interaction):
    """
    Shows an interactive, paginated, multi-select view for removing songs.
    """
    
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True, silent=SILENT_MESSAGES)
        return

    guild_id = interaction.guild_id
    is_kawaii = get_mode(guild_id)
    music_player = get_player(guild_id)

    if music_player.queue.empty():
        embed = Embed(description=get_messages("queue_empty", guild_id), color=0xFF9AA2 if is_kawaii else discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True, silent=SILENT_MESSAGES)
        return
    
    await interaction.response.defer()
    
    all_tracks = list(music_player.queue._queue)
    view = RemoveView(interaction, all_tracks)
    await view.update_view()
    
    embed = Embed(
        title=get_messages("remove_title", guild_id),
        description=get_messages("remove_description", guild_id),
        color=0xC7CEEA if is_kawaii else discord.Color.blue()
    )
    
    await interaction.followup.send(embed=embed, view=view, silent=SILENT_MESSAGES)

# ==============================================================================
# 6. DISCORD EVENTS
# ==============================================================================

@bot.event
async def on_voice_state_update(member, before, after):
    """
    Hyper-robust voice state manager that includes a silence loop
    for 24/7 mode and unified, explicit playback resume logic.
    """
    guild = member.guild
    vc = guild.voice_client

    if not vc or not vc.channel:
        return

    music_player = get_player(guild.id)
    guild_id = guild.id

    if member.id == bot.user.id and after.channel is None:
        if music_player.is_reconnecting or music_player.is_cleaning:
            return

        if music_player.silence_task and not music_player.silence_task.done():
            music_player.silence_task.cancel()

        if _24_7_active.get(guild_id, False):
            logger.warning(f"Bot was disconnected from guild {guild_id}, but 24/7 mode is active. Preserving player state.")
            music_player.voice_client = None
            if music_player.current_task and not music_player.current_task.done():
                music_player.current_task.cancel()
            return
        
        logger.info(f"Bot was disconnected from guild {guild_id}. Triggering full cleanup.")
        clear_audio_cache(guild_id)
        if music_player.current_task and not music_player.current_task.done():
            music_player.current_task.cancel()
        music_players[guild_id] = MusicPlayer()
        if guild_id in server_filters: del server_filters[guild_id]
        if guild_id in _24_7_active: del _24_7_active[guild_id]
        logger.info(f"Player for guild {guild_id} has been reset.")
        return

    bot_channel = vc.channel
    human_members = [m for m in bot_channel.members if not m.bot]

    if not member.bot and before.channel == bot_channel and after.channel != bot_channel:
        if len(human_members) == 0:
            logger.info(f"Bot is now alone in channel for guild {guild_id}.")
            if vc.is_playing() and not music_player.is_playing_silence:
                if music_player.playback_started_at:
                    elapsed_since_play = time.time() - music_player.playback_started_at
                    music_player.start_time += elapsed_since_play * music_player.playback_speed
                    music_player.playback_started_at = None
                vc.pause()
                logger.info(f"Playback paused for guild {guild_id}.")

            if _24_7_active.get(guild_id, False):
                if music_player.silence_task and not music_player.silence_task.done():
                    music_player.silence_task.cancel()
                music_player.silence_task = bot.loop.create_task(play_silence_loop(guild_id))
            else:
                await asyncio.sleep(60)
                if vc.is_connected() and len([m for m in vc.channel.members if not m.bot]) == 0:
                    await vc.disconnect()

    elif not member.bot and after.channel == bot_channel and before.channel != bot_channel:
        was_in_silence_mode = False
        if music_player.silence_task and not music_player.silence_task.done():
            logger.info(f"[{guild_id}] A user has returned. Stopping the silence loop.")
            music_player.silence_task.cancel()
            was_in_silence_mode = True
            await asyncio.sleep(0.2) 

        if (vc.is_paused() or was_in_silence_mode) and len(human_members) > 0:
            if not music_player.current_info:
                return

            if music_player.playback_started_at is None:
                music_player.playback_started_at = time.time()
            
            current_timestamp = music_player.start_time

            if music_player.is_current_live:
                logger.info(f"Resuming a live stream for guild {guild_id}. Triggering resync.")
                music_player.is_resuming_live = True
                bot.loop.create_task(play_audio(guild_id, is_a_loop=True)) 
            else:
                logger.info(f"Resuming track '{music_player.current_info.get('title')}' at {current_timestamp:.2f}s.")
                bot.loop.create_task(play_audio(guild_id, seek_time=current_timestamp, is_a_loop=True))

@bot.event
async def on_ready():
    logger.info(f"{bot.user.name} is online.")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands.")

        async def rotate_presence():
            while True:
                if not bot.is_ready() or bot.is_closed():
                    return

                statuses = [
                    ("/karaoke & /lyrics", discord.ActivityType.listening),
                    ("/play [link] ", discord.ActivityType.listening),
                    (f"{len(bot.guilds)} servers", discord.ActivityType.playing)
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
                        logger.error(f"Error changing presence: {e}")
                        await asyncio.sleep(5)

        bot.loop.create_task(rotate_presence())

    except Exception as e:
        logger.error(f"Error during command synchronization: {e}")

# ==============================================================================
# 7. BOT INITIALIZATION & RUN
# ==============================================================================

bot.start_time = time.time()
bot.run(os.getenv("DISCORD_TOKEN"))
