import html
import requests
import asyncio
from pyrogram.types import Message

from app import BOT, bot

API_URL = "https://official-joke-api.appspot.com/random_joke"
ERROR_VISIBLE_DURATION = 8

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
        await message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not fetch a joke.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
