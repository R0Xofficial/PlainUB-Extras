import asyncio
import html
from datetime import datetime, timezone
from pyrogram.types import Message, User

from app import BOT, bot

QUOTLY_BOT_ID = 1031952739
QUOTLY_TIMEOUT = 15
ERROR_VISIBLE_DURATION = 8

async def find_quotly_response_in_history(bot: BOT, timeout: int) -> Message | None:
    start_time = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout:
        try:
            async for last_message in bot.get_chat_history(QUOTLY_BOT_ID, limit=1):
                if last_message.date > start_time and (
                    not last_message.from_user or not last_message.from_user.is_self
                ):
                    return last_message
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return None


@bot.add_cmd(cmd=["q", "quote"])
async def quote_sticker_handler(bot: BOT, message: Message):
    """
    CMD: Q | QUOTE
    INFO: Creates a sticker/image by forwarding messages to @QuotLyBot.
    """
    if not message.replied:
        await message.reply("Please reply to a message to quote.", del_in=ERROR_VISIBLE_DURATION)
        return

    count = 1
    if message.input and message.input.isdigit():
        count = min(int(message.input), 10)

    progress_message = await message.reply(f"<code>Fetching {count} message(s)...</code>")
    
    messages_to_quote = []
    current_id = message.replied.id
    
    max_attempts = count + 20 
    attempts = 0

    while len(messages_to_quote) < count and attempts < max_attempts:
        try:
            msg = await bot.get_messages(message.chat.id, current_id)
            if msg:
                messages_to_quote.append(msg)
        except Exception:
            pass
        
        current_id += 1
        attempts += 1
    
    if not messages_to_quote:
        await progress_message.edit("Could not find any valid messages to quote.", del_in=ERROR_VISIBLE_DURATION)
        try: await message.delete()
        except: pass
        return

    await progress_message.edit(f"<code>Forwarding {len(messages_to_quote)} message(s) to @QuotLyBot...</code>")
    
    try:
        await bot.forward_messages(
            chat_id=QUOTLY_BOT_ID,
            from_chat_id=message.chat.id,
            message_ids=[msg.id for msg in messages_to_quote]
        )
        
        await asyncio.sleep(2)
        
        quotly_response = await find_quotly_response_in_history(bot, QUOTLY_TIMEOUT - 2)

        if quotly_response:
            await progress_message.delete()
            await message.delete()
            await quotly_response.forward(message.chat.id)
        else:
            raise asyncio.TimeoutError("@QuotLyBot did not respond in time.")

    except Exception as e:
        error_text = f"<b>Error:</b> Could not get a quote from @QuotLyBot.\n<code>{html.escape(str(e))}</code>"
        try:
            await progress_message.edit(error_text)
            await asyncio.sleep(ERROR_VISIBLE_DURATION)
            await progress_message.delete()
        except Exception: pass
