import os
import asyncio
import hashlib
import html
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

CHUNK_SIZE = 65536 
TEMP_DIR = "temp_downloads/"

@bot.add_cmd(cmd="hash")
async def hash_file_handler(bot: BOT, message: Message):
    """
    CMD: HASH
    INFO: Calculates hashes of a file by downloading it to a temporary directory.
    USAGE:
        .hash (reply to a file)
    """
    if not message.replied or not (media := message.replied.document or message.replied.video or message.replied.audio):
        await message.reply("Please reply to a file to calculate its hashes.", del_in=MEDIUM_TIMEOUT)
        return

    progress_msg = await message.reply(f"<code>Preparing to download '{getattr(media, 'file_name', 'media')}'...</code>")
    
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_file_path = os.path.join(TEMP_DIR, str(media.file_unique_id))

    try:
        last_reported_mb = -1
        async def progress_callback(current, total):
            nonlocal last_reported_mb
            current_mb = int(current / 1024 / 1024)
            if current_mb > last_reported_mb:
                try:
                    await progress_msg.edit(f"<code>Downloading... {current_mb} MB / {total / 1024 / 1024:.0f} MB</code>")
                    last_reported_mb = current_mb
                except MessageNotModified:
                    pass

        await bot.download_media(
            message=message.replied,
            file_name=temp_file_path,
            progress=progress_callback
        )
        
        await progress_msg.edit("<code>Download complete. Calculating hashes...</code>")

        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()

        with open(temp_file_path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                md5.update(chunk)
                sha1.update(chunk)
                sha256.update(chunk)

        md5_hash = md5.hexdigest()
        sha1_hash = sha1.hexdigest()
        sha256_hash = sha256.hexdigest()

        file_size = os.path.getsize(temp_file_path)
        if file_size < 1024**2: size_str = f"{file_size/1024:.2f} KB"
        elif file_size < 1024**3: size_str = f"{file_size/1024**2:.2f} MB"
        else: size_str = f"{file_size/1024**3:.2f} GB"

        response = (
            f"<b>File Details for:</b> <code>{html.escape(getattr(media, 'file_name', 'media'))}</code>\n\n"
            f"<b>Size:</b> <code>{size_str}</code>\n"
            f"<b>MD5:</b> <code>{md5_hash}</code>\n"
            f"<b>SHA1:</b> <code>{sha1_hash}</code>\n"
            f"<b>SHA256:</b> <code>{sha256_hash}</code>"
        )
        await progress_msg.edit(response)

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> An error occurred.\n<code>{e}</code>", del_in=LONG_TIMEOUT)
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
