import asyncio
import html
from datetime import datetime, timezone
from asyncio import TimeoutError
from pyrogram import filters
from pyrogram.types import Message, User

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

QUOTLY_BOT_ID = 1031952739
QUOTLY_TIMEOUT = 20

async def find_response_in_history(bot: BOT, chat_id: int, after_message_id: int, timeout: int) -> Message | None:
    start_time = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout:
        try:
            async for last_message in bot.get_chat_history(chat_id, limit=1):
                if last_message.id > after_message_id and (
                    not last_message.from_user or not last_message.from_user.is_self
                ):
                    return last_message
        except Exception:
            pass
        await asyncio.sleep(1)
    return None


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

    progress_message = await message.reply(f"<code>Processing {count} message(s)...</code>")
    
    start_id = message.replied.id
    message_ids = list(range(start_id, start_id + count))

    try:
        last_message_id = 0
        async for last_msg in bot.get_chat_history(QUOTLY_BOT_ID, limit=1):
            last_message_id = last_msg.id

        await bot.forward_messages(
            chat_id=QUOTLY_BOT_ID,
            from_chat_id=message.chat.id,
            message_ids=message_ids
        )
        
        await progress_message.edit("<code>Waiting for @QuotLyBot's response...</code>")

        quotly_response = await find_response_in_history(
            bot,
            chat_id=QUOTLY_BOT_ID,
            after_message_id=last_message_id,
            timeout=QUOTLY_TIMEOUT
        )

        if not quotly_response:
            raise TimeoutError()

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
