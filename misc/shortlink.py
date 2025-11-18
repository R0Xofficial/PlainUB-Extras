import html
import requests
import asyncio
from pyrogram.types import LinkPreviewOptions, Message

from app import BOT, bot

API_URL = "https://tinyurl.com/api-create.php"
ERROR_VISIBLE_DURATION = 8

def sync_shorten(url: str) -> str:
    """
    Synchronous shorten function using tinyurl.com's simple text API.
    """
    params = {"url": url}
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.text

@bot.add_cmd(cmd=["sl", "short", "shortlink"])
async def shortlink_handler(bot: BOT, message: Message):
    """
    CMD: SL | SHORT | SHORTLINK
    INFO: Shortens a long URL. Success messages are permanent, errors disappear.
    """
    url_to_shorten = ""

    if message.input:
        url_to_shorten = message.input
    elif message.replied:
        url_to_shorten = message.replied.text or message.replied.caption
    
    if not url_to_shorten:
        await message.reply("Please provide a URL.")
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await message.delete()
        return

    progress_message = await message.reply("<code>Shortening link...</code>")
    
    try:
        shortened_url = await asyncio.to_thread(sync_shorten, url_to_shorten)
        
        if shortened_url and shortened_url.startswith("http"):
            final_text = (
                f"<b>Original URL:</b> <code>{html.escape(url_to_shorten)}</code>\n"
                f"<b>Shortened URL:</b> <code>{shortened_url}</code>"
            )
            await progress_message.edit(
                final_text,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
            await message.delete()
            return
        
        else:
            error_text = f"<b>API Error:</b> Received an invalid response from the server."
            await progress_message.edit(error_text)

    except Exception as e:
        error_text = f"<b>An error occurred:</b>\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text)

    await asyncio.sleep(ERROR_VISIBLE_DURATION)
    await progress_message.delete()
