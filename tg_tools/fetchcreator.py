import html
from pyrogram.types import Message, User, Chat, ReplyParameters, LinkPreviewOptions
from pyrogram.enums import ChatType

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

@bot.add_cmd(cmd=["fetchcreator", "fcreator", "fc"])
async def forward_info_handler(bot: BOT, message: Message):
    """
    CMD: FETCHCREATOR / FCREATOR / FC
    INFO: Gets information about the original sender of a forwarded message.
    USAGE:
        .fc (in reply to a forwarded message)
    """
    replied_msg = message.replied
    
    if not replied_msg:
        await message.reply("Please reply to a message.", del_in=MEDIUM_TIMEOUT)
        return
        
    if not replied_msg.forward_date:
        await message.reply("The replied-to message is not a forward.", del_in=LONG_TIMEOUT)
        return

    info_lines = ["<b>Forward Origin Info:</b>"]
    
    if replied_msg.forward_from:
        user: User = replied_msg.forward_from
        
        if user.is_deleted:
            info_lines.append(f"• <b>Type:</b> Deleted Account 💀")
            info_lines.append(f"• <b>ID:</b> <code>{user.id}</code>")
            info_lines.append(f"• <b>Name:</b> Deleted Account")
        else:
            info_lines.append(f"• <b>Type:</b> User 👤")
            info_lines.append(f"• <b>ID:</b> <code>{user.id}</code>")
            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"
            info_lines.append(f"• <b>Name:</b> {html.escape(name)}")
            if user.username:
                info_lines.append(f"• <b>Username:</b> @{user.username}")
            info_lines.append(f"• <b>Permalink:</b> {user.mention('Click Here')}")

    elif replied_msg.forward_from_chat:
        chat: Chat = replied_msg.forward_from_chat
        
        info_lines.append(f"• <b>Type:</b> {'Channel 📢' if chat.type == ChatType.CHANNEL else 'Group 👥'}")
        
        info_lines.append(f"• <b>ID:</b> <code>{chat.id}</code>")
        info_lines.append(f"• <b>Name:</b> {html.escape(chat.title)}")
        
        if chat.username:
            info_lines.append(f"• <b>Username:</b> @{chat.username}")
            info_lines.append(f"• <b>Chat Link:</b> <a href='https://t.me/{chat.username}'>Click Here</a>")
        else:
            info_lines.append("• <b>Chat Link:</b> Not available (private)")
            
    else:
        info_lines.append("Could not determine the original sender. Possible that the message creator has disabled profile linking for forwarded messages.")

    await bot.send_message(
        chat_id=message.chat.id,
        text="\n".join(info_lines),
        reply_parameters=ReplyParameters(message_id=replied_msg.id),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
