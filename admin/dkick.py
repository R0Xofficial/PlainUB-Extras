import html
import asyncio
from pyrogram.types import Message, User

from app import BOT, bot

from app.modules.settings import SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT

@bot.add_cmd(cmd="dkick")
async def dkick_handler(bot: BOT, message: Message):
    """
    CMD: DKICK
    INFO: Deletes the replied-to message and kicks the user.
    USAGE:
        .dkick [reason] (in reply to a message)
    """
    if not message.chat._raw.admin_rights:
        await message.reply("I need admin rights to perform this action.", del_in=MEDIUM_TIMEOUT)
        return

    user, reason = await message.extract_user_n_reason()

    if not isinstance(user, User):
        await message.reply(user, del_in=LONG_TIMEOUT)
        return

    try:
        if message.replied:
            await message.replied.delete()
        
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=user.id)
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=user.id)

        await message.reply(text=f"Kicked: {user.mention}\nReason: {reason}")
    
    except Exception as e:
        await message.reply(text=str(e), del_in=LONG_TIMEOUT)
