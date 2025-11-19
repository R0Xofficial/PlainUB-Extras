import html
from pyrogram.types import Message, User

from app import BOT, bot

@bot.add_cmd(cmd=["rban", "runban"])
async def remote_ban_handler(bot: BOT, message: Message):
    """
    CMD: RBAN / RUNBAN
    INFO: Ban user remotely.
    USAGE:
        .rban [ID/username/reply] [ID/chatname/link] [reason]
        .runban [ID/username/reply] [ID/chatname/link] [reason]
    """
    if not message.input or len(message.input.split()) < 2:
        await message.reply(f"<b>Usage:</b> <code>.{message.cmd} [user] [chat] [reason]</code>", del_in=10)
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
        await message.reply(f"<b>Error:</b> Could not find user or chat.\n<code>{html.escape(str(e))}</code>", del_in=10)
        return

    if not isinstance(target_user, User):
        await message.reply("<b>Error:</b> Invalid user specified.", del_in=10)
        return

    action = bot.ban_chat_member if message.cmd == "rban" else bot.unban_chat_member
    action_str = f"{message.cmd[1:].capitalize()}ned"
    
    try:
        await action(chat_id=target_chat.id, user_id=target_user.id)
        
        confirmation_text = f"{action_str}: {target_user.mention}\nReason: {reason}"
        
        await bot.send_message(target_chat.id, confirmation_text)
        await message.reply(f"Remote {action_str}: {target_user.mention}\nChat: {html.escape(target_chat.title)}\nReason: {reason}")
        
    except Exception as e:
        await message.reply(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=15)
