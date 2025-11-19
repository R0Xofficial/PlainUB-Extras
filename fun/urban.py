import html
import requests
import asyncio
from pyrogram.types import LinkPreviewOptions, Message

from app import BOT, bot

API_URL = "http://api.urbandictionary.com/v0/define"
ERROR_VISIBLE_DURATION = 8

def safe_escape(text: str) -> str:
    escaped_text = html.escape(str(text))
    return escaped_text.replace("&#x27;", "’")

def sync_urban_search(term: str) -> dict | None:
    """Synchronously searches Urban Dictionary for a term."""
    params = {"term": term}
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    if data and data.get("list"):
        return data["list"][0]
    return None


@bot.add_cmd(cmd=["ud", "urban"])
async def urban_dictionary_handler(bot: BOT, message: Message):
    """
    CMD: UD | URBAN
    INFO: Searches for a definition on Urban Dictionary.
    USAGE: .ud [term]
    """
    
    term_to_search = message.input
    if not term_to_search:
        await message.reply("What term should I look up? Usage: `.ud yeet`", del_in=ERROR_VISIBLE_DURATION)
        return

    progress_message = await message.reply(f"<code>Searching Urban Dictionary for: {safe_escape(term_to_search)}...</code>")

    try:
        result = await asyncio.to_thread(sync_urban_search, term_to_search)
        
        if result:
            word = result.get("word", "N/A")
            definition = result.get("definition", "No definition found.").replace("[", "").replace("]", "")
            example = result.get("example", "No example provided.").replace("[", "").replace("]", "")
            permalink = result.get("permalink", "#")
            
            final_text = (
                f"<b>📖 Urban Definition for: <a href='{permalink}'>{safe_escape(word)}</a></b>\n\n"
                f"<b>Meaning:</b>\n<blockquote expandable>{safe_escape(definition)}</blockquote>\n\n"
                f"<b>Example:</b>\n<blockquote expandable>{safe_escape(example)}</blockquote>"
            )
            
            await progress_message.edit(
                final_text,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )

        else:
            error_text = f"Could not find a definition for <code>{safe_escape(term_to_search)}</code>."
            await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)

    except Exception as e:
        error_text = f"<b>An error occurred:</b>\n<code>{safe_escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
