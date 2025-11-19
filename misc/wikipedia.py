import html
import wikipediaapi
import asyncio
from pyrogram.types import LinkPreviewOptions, Message

from app import BOT, bot

ERROR_VISIBLE_DURATION = 8
WIKI_LANG = "en"
USER_AGENT = "MyCoolUserBot/1.0 (https://github.com/telegram)"
wiki_api = wikipediaapi.Wikipedia(language=WIKI_LANG, user_agent=USER_AGENT)

def safe_escape(text: str) -> str:
    escaped_text = html.escape(str(text))
    return escaped_text.replace("&#x27;", "’")

def sync_wiki_search(query: str) -> tuple[str, str, str] | None:
    """Synchronous function to search the English Wikipedia."""
    page = wiki_api.page(query)

    if page.exists():
        summary = page.summary[:350]
        if len(page.summary) > 350:
            summary = summary.rsplit(' ', 1)[0] + "..."
        return page.title, summary, page.fullurl
    return None

@bot.add_cmd(cmd=["wiki", "wikipedia"])
async def wiki_handler(bot: BOT, message: Message):
    """
    CMD: WIKI | WIKIPEDIA
    INFO: Searches for a page on the English Wikipedia.
    USAGE: .wiki [query]
    """
    
    query = message.input
    if not query:
        await message.reply("Please provide a search query. Usage: `.wiki Python (programming language)`", del_in=ERROR_VISIBLE_DURATION)
        return

    progress_message = await message.reply(f"<code>Searching Wikipedia for: {safe_escape(query)}...</code>")

    try:
        result = await asyncio.to_thread(sync_wiki_search, query)
        
        if result:
            title, summary, url = result
            final_text = (
                f"<b>📖 Wikipedia of: <a href='{url}'>{safe_escape(title)}</a></b>\n\n"
                f"{safe_escape(summary)}"
            )
            await progress_message.edit(final_text, link_preview_options=LinkPreviewOptions(is_disabled=True))
        else:
            error_text = f"Could not find any Wikipedia page for <code>{safe_escape(query)}</code>."
            await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    except Exception as e:
        error_text = f"<b>An error occurred:</b>\n<code>{safe_escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
