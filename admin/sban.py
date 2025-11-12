from pyrogram.types import Message, User

from app import BOT, bot

@bot.add_cmd(cmd="sban")
async def silent_ban_handler(bot: BOT, message: Message) -> None:
    """
    CMD: SBAN
    INFO: Silently bans a user without sending a confirmation message.
    USAGE:
        .sban [ID/username/reply]
    """
    if not message.chat._raw.admin_rights:
        return

    user, _ = await message.extract_user_n_reason()

    if not isinstance(user, User):
        return

    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=user.id)
    except Exception:
        pass
