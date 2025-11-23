import asyncio
import html
from asyncio import TimeoutError
from pyrogram import filters
from pyrogram.types import Message, User

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

QUOTLY_BOT_ID = 1031952739
QUOTLY_TIMEOUT = 20

@bot.add_cmd(cmd=["q", "quote"])
async def quote_sticker_handler(bot: BOT, message: Message):
    """
    CMD: Q | QUOTE
    INFO: Creates a sticker/image by forwarding messages to @QuotLyBot.
    USAGE:
        .q (quotes the replied message)
        .q [count] (quotes a sequence of 'count' messages)
    """
    if not message.replied:
        await message.reply("Please reply to a message to quote.", del_in=MEDIUM_TIMEOUT)
        return

    count = 1
    if message.input and message.input.isdigit():
        count = min(int(message.input), 15)

    progress_message = await message.reply(f"<code>Fetching {count} message(s)...</code>")
    
    start_id = message.replied.id
    message_ids = list(range(start_id, start_id + count))

    try:
        await bot.forward_messages(
            chat_id=QUOTLY_BOT_ID,
            from_chat_id=message.chat.id,
            message_ids=message_ids
        )
        
        await progress_message.edit("<code>Waiting for @QuotLyBot's response...</code>")

        quotly_response = await bot.listen(
            chat_id=QUOTLY_BOT_ID,
            filters=filters.user(QUOTLY_BOT_ID),
            timeout=QUOTLY_TIMEOUT
        )

        await quotly_response.copy(message.chat.id)
        await progress_message.delete()

    except TimeoutError:
        await progress_message.edit(
            "<b>Error:</b> @QuotLyBot did not respond in time.", 
            del_in=LONG_TIMEOUT
        )
    except Exception as e:
        error_text = f"<b>Error:</b> Could not get a quote.\n<code>{html.escape(str(e))}</code>"
        try:
            await progress_message.edit(error_text, del_in=LONG_TIMEOUT)
        except Exception:
            pass
