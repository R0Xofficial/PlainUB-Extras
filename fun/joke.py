import html
import requests
import asyncio
from pyrogram.types import Message

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

API_URL = "https://official-joke-api.appspot.com/random_joke"

def safe_escape(text: str) -> str:
    escaped_text = html.escape(str(text))
    return escaped_text.replace("&#x27;", "’")

def sync_get_joke() -> dict:
    """Synchronously fetches a random joke."""
    response = requests.get(API_URL)
    response.raise_for_status()
    return response.json()

@bot.add_cmd(cmd="joke")
async def joke_handler(bot: BOT, message: Message):
    """
    CMD: JOKE
    INFO: Tells you a random joke.
    """
    
    progress_message = await message.reply("<code>Finding a good joke...</code>")
    
    try:
        joke_data = await asyncio.to_thread(sync_get_joke)
        
        setup = joke_data.get("setup")
        punchline = joke_data.get("punchline")
        
        if not setup or not punchline:
            raise ValueError("Invalid joke format received.")
            
        await progress_message.edit(f"<b>{html.escape(setup)}</b>")
        await asyncio.sleep(3)
        await progress_message.edit(
            f"<b>{html.escape(setup)}</b>\n\n<i>...{html.escape(punchline)}</i>"
        )

    except Exception as e:
        error_text = f"<b>Error:</b> Could not fetch a joke.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=LONG_TIMEOUT)
