import html
from pyrogram.types import Message, User

from app import BOT, bot

from app.modules.settings import SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT

@bot.add_cmd(cmd="dban")
async def dban_handler(bot: BOT, message: Message):
    """
    CMD: DBAN
    INFO: Deletes the replied-to message and bans the user.
    USAGE:
        .dban [reason] (in reply to a message)
    """
    if not message.chat._raw.admin_rights:
        await message.reply("I need admin rights to perform this action.", del_in=MEDIUM_TIMEOUT)
        return

    user, reason = await message.extract_user_n_reason()

    if not isinstance(user, User):
        await message.reply(user, del_in=10)
        return

    try:
        if message.replied:
            await message.replied.delete()
        
        await bot.ban_chat_member(message.chat.id, user.id)
        
        await message.reply(text=f"Banned: {user.mention}\nReason: {reason}")
    
    except Exception as e:
        await message.reply(text=str(e), del_in=LONG_TIMEOUT)
