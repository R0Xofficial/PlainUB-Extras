import html
from pyrogram.types import Message, User, ChatPermissions

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

@bot.add_cmd(cmd=["rmute", "runmute"])
async def remote_mute_handler(bot: BOT, message: Message):
    """
    CMD:
    INFO: Mute user remotely.
    USAGE:
        .rmute [ID/username/reply] [ID/chatname/link] [reason]
        .runmute [ID/username/reply] [ID/chatname/link] [reason]
    """
    if not message.input or len(message.input.split()) < 2:
        await message.reply(f"<b>Usage:</b> <code>.{message.cmd} [user] [chat] [reason]</code>", del_in=MEDIUM_TIMEOUT)
        return

    parts = message.input.split(maxsplit=2)
    user_identifier = parts[0]
    chat_identifier_raw = parts[1]
    reason = parts[2] if len(parts) > 2 else "No reason provided."

    if "t.me/" in chat_identifier_raw:
        chat_identifier = chat_identifier_raw.split('/')[-1]
    else:
        chat_identifier = chat_identifier_raw

    try:
        target_user = await bot.get_users(user_identifier)
        target_chat = await bot.get_chat(chat_identifier)
    except Exception as e:
        await message.reply(f"<b>Error:</b> Could not find user or chat.\n<code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
        return

    if not isinstance(target_user, User):
        await message.reply("<b>Error:</b> Invalid user specified.", del_in=LONG_TIMEOUT)
        return

    action_str = ""
    try:
        if message.cmd == "rmute":
            await bot.restrict_chat_member(
                chat_id=target_chat.id,
                user_id=target_user.id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            action_str = "Muted"
        else:
            await bot.unban_chat_member(chat_id=target_chat.id, user_id=target_user.id)
            action_str = "Unmuted"

        confirmation_text = f"{action_str}: {target_user.mention}\nReason: {reason}"

        await bot.send_message(target_chat.id, confirmation_text)
        await message.reply(f"Remote {action_str}: {target_user.mention}\nChat: {html.escape(target_chat.title)}\nReason: {reason}")

    except Exception as e:
        await message.reply(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
