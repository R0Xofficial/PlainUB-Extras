from pyrogram.types import Message, User, ChatPermissions

from app import BOT, bot

@bot.add_cmd(cmd="smute")
async def silent_mute_handler(bot: BOT, message: Message):
    """
    CMD: SMUTE
    INFO: Silently mutes a user without sending a confirmation message.
    USAGE:
        .smute [ID/username/reply]
    """
    if not message.chat._raw.admin_rights:
        return

    user, _ = await message.extract_user_n_reason()

    if not isinstance(user, User):
        return

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except Exception:
        pass
