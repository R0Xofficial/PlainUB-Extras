import asyncio
import hashlib
import html
from pyrogram.types import Message

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

CHUNK_SIZE = 65536

@bot.add_cmd(cmd="hash")
async def hash_file_handler(bot: BOT, message: Message):
    """
    CMD: HASH
    INFO: Calculates and displays the MD5, SHA1, and SHA256 hashes of a file.
    USAGE:
        .hash (reply to a file)
    """
    if not message.replied or not message.replied.document:
        await message.reply("Please reply to a file to calculate its hashes.", del_in=MEDIUM_TIMEOUT)
        return

    doc = message.replied.document
    progress_msg = await message.reply(f"<code>Downloading file to calculate hashes...</code>")
    
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    
    file_size = 0
    
    try:
        async for chunk in bot.stream_media(message.replied, limit=CHUNK_SIZE):
            if chunk:
                file_size += len(chunk)
                md5.update(chunk)
                sha1.update(chunk)
                sha256.update(chunk)
            if file_size % (10 * 1024 * 1024) == 0:
                await progress_msg.edit(f"<code>Processing...</code>")

        md5_hash = md5.hexdigest()
        sha1_hash = sha1.hexdigest()
        sha256_hash = sha256.hexdigest()

        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024**2:
            size_str = f"{file_size/1024:.2f} KB"
        elif file_size < 1024**3:
            size_str = f"{file_size/1024**2:.2f} MB"
        else:
            size_str = f"{file_size/1024**3:.2f} GB"

        response = (
            f"<b>File Details for:</b> <code>{html.escape(doc.file_name)}</code>\n\n"
            f"<b>Size:</b> <code>{size_str}</code>\n"
            f"<b>MD5:</b> <code>{md5_hash}</code>\n"
            f"<b>SHA1:</b> <code>{sha1_hash}</code>\n"
            f"<b>SHA256:</b> <code>{sha256_hash}</code>"
        )
        await progress_msg.edit(response)

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> An error occurred while processing the file.\n<code>{e}</code>", del_in=LARGE_TIMEOUT)
