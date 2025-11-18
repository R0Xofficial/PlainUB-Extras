import html
import asyncio
from pyrogram.types import Message

from app import BOT, bot

async def _delayed_leave(chat_id: int | str):
    await asyncio.sleep(1)
    await bot.leave_chat(chat_id)

@bot.add_cmd(cmd="leave")
async def leave_chat_handler(bot: BOT, message: Message):
    """
    CMD: LEAVE
    INFO: Leaves a chat or channel.
    USAGE:
        .leave (leaves the current chat)
        .leave [ID/@chatname/link] (leaves a specific chat)
    """
    
    try:
        if message.input:
            chat_identifier = message.input.strip()
            
            if "t.me/" in chat_identifier:
                chat_identifier = chat_identifier.split('/')[-1]

            try:
                chat_identifier_for_api = int(chat_identifier)
            except ValueError:
                chat_identifier_for_api = chat_identifier

            await bot.leave_chat(chat_identifier_for_api)
            
            confirmation_msg = await message.reply(
                f"<code>Successfully left</code>"
            )
            await asyncio.sleep(8)
            await confirmation_msg.delete()
        else:
            asyncio.create_task(_delayed_leave(message.chat.id))

    except Exception as e:
        await message.reply(f"<b>Error:</b> Could not leave chat.\n<code>{html.escape(str(e))}</code>", del_in=10)
