import asyncio
import html
from googlesearch import search
from pyrogram.types import LinkPreviewOptions, Message

from app import BOT, bot

ERROR_VISIBLE_DURATION = 8

def sync_search(query: str):
    """Synchronous search function to be run in a separate thread."""
    return list(search(query, num_results=5, sleep_interval=1))

@bot.add_cmd(cmd=["g", "google"])
async def google_search_handler(bot: BOT, message: Message):
    """
    CMD: G | GOOGLE
    INFO: Performs a Google search. Success messages are permanent, errors disappear.
    """
    query = message.input
    if not query:
        await message.reply("Please provide a search query.", del_in=ERROR_VISIBLE_DURATION)
        return

    progress_message = await message.reply(f"<code>Searching Google for: {query}</code>...")

    try:
        search_results = await asyncio.to_thread(sync_search, query)
        
        if not search_results:
            await progress_message.edit(f"No results found for <code>{query}</code>.", del_in=ERROR_VISIBLE_DURATION)
            return

        output_str = f"<b>🔎 Search results for:</b> <code>{html.escape(query)}</code>\n\n"
        for i, link in enumerate(search_results):
            output_str += f"{i+1}. <a href='{link}'>{link}</a>\n"
        
        await progress_message.edit(
            output_str,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    except Exception as e:
        error_text = f"<b>An error occurred while searching:</b>\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
