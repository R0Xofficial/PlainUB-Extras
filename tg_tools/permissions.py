import html
from pyrogram.types import Message, LinkPreviewOptions
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import PeerIdInvalid, UserNotParticipant

from app import BOT, bot

def safe_escape(text: str) -> str:
    if not isinstance(text, str):
        return ""
    escaped_text = html.escape(text)
    return escaped_text.replace("&#x27;", "’")

@bot.add_cmd(cmd=["perms", "permissions"])
async def check_permissions_handler(bot: BOT, message: Message):
    """
    CMD: PERMS / PERMISSION
    INFO: Checks a user's permissions in a group.
    USAGE:
          .perms (Check your permissions in this group)
          .perms [user] (Check a user's permissions in this group)
          .perms [chat] [user] (Check a user's permissions in another group)
    """
    target_chat_id = message.chat.id
    target_user_id = None
    
    args = message.input.split()

    if len(args) >= 2:
        target_chat_id = args[0]
        target_user_id = args[1]
    elif len(args) == 1:
        if message.replied:
            target_chat_id = args[0]
            target_user_id = message.replied.from_user.id
        else:
            target_user_id = args[0]
    else:
        if message.replied:
            target_user_id = message.replied.from_user.id
        else:
            target_user_id = message.from_user.id

    try:
        chat = await bot.get_chat(target_chat_id)
        user = await bot.get_users(target_user_id)
        member = await bot.get_chat_member(chat.id, user.id)
    except PeerIdInvalid:
        await message.reply("Could not find the specified chat or user. Please check the ID/username.")
        return
    except UserNotParticipant:
        await message.reply(f"User {user.mention} is not a member of the chat {chat.title}.")
        return
    except Exception as e:
        await message.reply(f"An error occurred: `{e}`")
        return

    response_lines = [
        f"<b>Permissions for {user.mention}</b>",
        f"<b>in Chat:</b> {safe_escape(chat.title)}\n"
    ]

    status_map = {
        ChatMemberStatus.OWNER: "Creator (Owner)",
        ChatMemberStatus.ADMINISTRATOR: "Administrator",
        ChatMemberStatus.MEMBER: "Member",
        ChatMemberStatus.RESTRICTED: "Restricted",
        ChatMemberStatus.LEFT: "Left",
        ChatMemberStatus.BANNED: "Banned"
    }
    status_str = status_map.get(member.status, "Unknown Status")
    
    response_lines.append(f"• <b>Status:</b> {status_str}")
    if member.custom_title:
        response_lines.append(f"• <b>Custom Title:</b> {safe_escape(member.custom_title)}")

    if member.status == ChatMemberStatus.ADMINISTRATOR and member.privileges:
        perms = member.privileges
        perm_list = [
            ("Manage Chat", perms.can_manage_chat),
            ("Delete Messages", perms.can_delete_messages),
            ("Manage Video Chats", perms.can_manage_video_chats),
            ("Restrict Members", perms.can_restrict_members),
            ("Change Info", perms.can_change_info),
            ("Invite Users", perms.can_invite_users),
            ("Pin Messages", perms.can_pin_messages),
            ("Promote Members", perms.can_promote_members),
            ("Post Stories", perms.can_post_stories),
            ("Edit Stories", perms.can_edit_stories),
            ("Delete Stories", perms.can_delete_stories),
            ("Remain Anonymous", perms.is_anonymous)
        ]
        
        granted_perms = [text for text, has_perm in perm_list if has_perm]
        
        if granted_perms:
            perm_details = "\n".join([f"  – {perm}" for perm in granted_perms])
            response_lines.append(f"• <b>Permissions:</b>\n<blockquote expandable>{perm_details}</blockquote>")
        else:
            response_lines.append("• <b>Permissions:</b> None")

    elif member.status == ChatMemberStatus.OWNER:
        response_lines.append("• <b>Permissions:</b>\n<blockquote expandable>  – All Permissions (Creator)</blockquote>")

    elif member.status == ChatMemberStatus.RESTRICTED and member.permissions:
        perms = member.permissions
        perm_list = {
            "Send Messages": perms.can_send_messages,
            "Send Media": perms.can_send_media_messages,
            "Send Stickers/GIFs": perms.can_send_stickers and perms.can_send_animations,
            "Send Polls": perms.can_send_polls,
            "Embed Links": perms.can_add_web_page_previews,
            "Add Members": perms.can_invite_users,
            "Pin Messages": perms.can_pin_messages,
            "Change Chat Info": perms.can_change_info
        }

        denied_perms = [text for text, has_perm in perm_list.items() if not has_perm]
        
        if denied_perms:
            perm_details = "\n".join([f"  – {perm}" for perm in denied_perms])
            response_lines.append(f"• <b>Restrictions (Cannot):</b>\n<blockquote expandable>{perm_details}</blockquote>")
        
        if member.until_date:
            response_lines.append(f"• <b>Restricted Until:</b> {member.until_date.strftime('%d %b %Y, %H:%M UTC')}")
        else:
            response_lines.append("• <b>Restricted Until:</b> Forever")

    await message.reply("\n".join(response_lines), link_preview_options=LinkPreviewOptions(is_disabled=True))
