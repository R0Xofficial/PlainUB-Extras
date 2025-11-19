import html
from pyrogram.types import Message, ChatPermissions, User

from app import BOT, bot

from app.modules.settings import SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT

@bot.add_cmd(cmd="dmute")
async def dmute_handler(bot: BOT, message: Message):
    """
    CMD: DMUTE
    INFO: Deletes the replied-to message and mutes the user.
    USAGE:
        .dmute [reason] (in reply to a message)
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
        
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_pin_messages=False,
                can_invite_users=False,
                can_change_info=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
        )
        
        await message.reply(text=f"Muted: {user.mention}\nReason: {reason}")
    
    except Exception as e:
        await message.reply(text=str(e), del_in=LONG_TIMEOUT)
