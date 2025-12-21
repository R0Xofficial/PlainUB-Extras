import asyncio
import shutil
from functools import partial
from pathlib import Path
from time import time
from urllib.parse import urlparse

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import InputMediaAudio

from app import BOT, Message

domains = [
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtube-nocookie.com",
    "music.youtube.com",
]


def is_yt_url(url: str) -> bool:
    return urlparse(url).netloc in domains


def extract_link_from_reply(message: Message) -> str | None:
    if not message:
        return None

    for link in message.text_list:
        if is_yt_url(link):
            return link

    for entity in message.entities or []:
        if entity.type == MessageEntityType.TEXT_LINK and is_yt_url(entity.url):
            return entity.url

    return None


def download_sync(query: str, path: Path) -> dict:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(path / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "noplaylist": True,
        "writethumbnail": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        if not query.startswith("http"):
            query = f"ytsearch:{query}"

        info = ydl.extract_info(query, download=True)

        if "entries" in info:
            return info["entries"][0]
        return info


@BOT.add_cmd(cmd=["song", "sg"])
async def song_dl(bot: BOT, message: Message):
    query = extract_link_from_reply(message.replied) or message.filtered_input

    if not query:
        await message.reply("Give a song name or link to download.")
        return

    response = await message.reply("Searching....")

    download_path = Path("downloads") / str(time())
    download_path.mkdir(parents=True, exist_ok=True)

    try:
        loop = asyncio.get_running_loop()
        song_info = await loop.run_in_executor(
            None, partial(download_sync, query, download_path)
        )

        if not song_info:
            await response.edit("Song Not found.")
            return

        audio_files = list(download_path.glob("*.mp3"))
        if not audio_files:
            await response.edit("Download failed.")
            return

        audio_file = audio_files[0]
        
        thumb_files = list(download_path.glob("*.jpg")) + list(download_path.glob("*.webp"))
        thumb = str(thumb_files[0]) if thumb_files else None

        await response.edit(f"`Uploading {audio_file.name}....`")

        await response.edit_media(
            InputMediaAudio(
                media=str(audio_file),
                caption=f"<a href='{song_info.get('webpage_url')}'>{song_info.get('title')}</a>",
                duration=int(song_info.get("duration", 0)),
                performer=song_info.get("uploader"),
                title=song_info.get("title"),
                thumb=thumb,
            )
        )

    except Exception as e:
        await response.edit(f"Error: {e}")

    finally:
        if download_path.exists():
            shutil.rmtree(download_path, ignore_errors=True)
