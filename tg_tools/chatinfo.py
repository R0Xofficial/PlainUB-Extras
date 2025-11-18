import os
import html
import shutil
from pyrogram.enums import ChatType
from pyrogram.types import Chat, Message, LinkPreviewOptions, ReplyParameters

from app import BOT, bot

TEMP_CINFO_DIR = "temp_cinfo_photos/"

def safe_escape(text: str) -> str:
    return html.escape(str(text)) if text else ""

async def format_chat_info(chat: Chat, is_full: bool) -> tuple[str, str | None]:
    if is_full:
        info_lines = ["<b>Chat Info:</b>"]
        info_lines.extend([
            f"• <b>Title:</b> {safe_escape(chat.title)}",
            f"• <b>ID:</b> <code>{chat.id}</code>",
        ])
        type_map = {
            ChatType.GROUP: "Group 👥",
            ChatType.SUPERGROUP: "Supergroup 👥",
            ChatType.CHANNEL: "Channel 📢"
        }
        info_lines.append(f"• <b>Type:</b> {type_map.get(chat.type, '<i>Unknown</i>')}")

        if chat.username:
            info_lines.append(f"• <b>Username:</b> @{chat.username}")
        
        if chat.description:
            desc = chat.description
            info_lines.append(f"• <b>Description:</b> {safe_escape(desc[:200] + '...' if len(desc) > 200 else desc)}")
            
        if chat.members_count:
            info_lines.append(f"• <b>Members:</b> {chat.members_count}")

        flags = [flag for c, flag in [
            (chat.is_verified, "Verified ✅"),
            (chat.is_scam, "Scam ‼️"),
            (chat.is_restricted, "Restricted 🔞")
        ] if c]
        if flags:
            info_lines.append(f"• <b>Flags:</b> {', '.join(flags)}")

        if chat.dc_id:
            info_lines.append(f"• <b>Data Center:</b> {chat.dc_id}")
            
        if chat.linked_chat:
            info_lines.append(f"• <b>Linked Chat ID:</b> <code>{chat.linked_chat.id}</code>")
        if chat.username:
            info_lines.append(f"\n<b>Permalink:</b> <a href='https://t.me/{chat.username}'>Click Here</a>")
    else:
        info_lines = [
            "<b>Chat info:</b>",
            f"• <b>Title:</b> {safe_escape(chat.title)}",
            f"• <b>ID:</b> <code>{chat.id}</code>"
        ]
        if chat.username:
            info_lines.append(f"• <b>Username:</b> @{chat.username}")
        if chat.members_count:
            info_lines.append(f"• <b>Members:</b> {chat.members_count}")
        if chat.username:
            info_lines.append(f"\n<b>Permalink:</b> <a href='https://t.me/{chat.username}'>Click Here</a>")

    photo_id = chat.photo.big_file_id if is_full and chat.photo else None
    return "\n".join(info_lines), photo_id

@bot.add_cmd(cmd=["cinfo", "chatinfo"])
async def chat_info_handler(bot: BOT, message: Message):
    progress_msg = await message.reply("<code>Fetching chat information...</code>")

    is_full_mode = "-full" in message.text.split()
    target_identifier = message.input.replace("-full", "").strip() if message.input else None

    if not target_identifier:
        target_identifier = message.chat.id
    elif "t.me/" in target_identifier:
        target_identifier = target_identifier.split('/')[-1]

    try:
        target_chat = await bot.get_chat(target_identifier)
        if target_chat.type == ChatType.PRIVATE:
            return await progress_msg.edit("This command is for groups and channels. Use <code>.info</code> for users.", del_in=8)
        
        final_text, photo_id = await format_chat_info(target_chat, is_full_mode)

        if photo_id:
            photo_path = ""
            try:
                os.makedirs(TEMP_CINFO_DIR, exist_ok=True)
                photo_path = await bot.download_media(photo_id, file_name=TEMP_CINFO_DIR)
                
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=photo_path,
                    caption=final_text,
                    reply_parameters=ReplyParameters(message_id=message.id)
                )
                await progress_msg.delete()
            finally:
                if os.path.exists(photo_path):
                    shutil.rmtree(TEMP_CINFO_DIR, ignore_errors=True)
        else:
            await progress_msg.edit(
                final_text,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> Could not find the specified chat.\n<code>{safe_escape(str(e))}</code>", del_in=10)
