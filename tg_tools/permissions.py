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
    CMD: PERMS / PERMISSIONS
    INFO: Checks a user's permissions in a group.
    USAGE:
          .perms (Check your permissions in this group)
          .perms [ID/username/reply] (Check a user's permissions in this group)
    """
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("This command can only be used in group chats.")
        return

    target_user = None
    if message.replied:
        target_user = message.replied.from_user
    elif message.input:
        try:
            target_user = await bot.get_users(message.input)
        except Exception:
            await message.reply("Could not find the specified user.")
            return
    else:
        target_user = message.from_user

    try:
        member = await bot.get_chat_member(message.chat.id, target_user.id)
    except UserNotParticipant:
        await message.reply(f"User {target_user.mention} is not a member of this chat.")
        return
    except Exception as e:
        await message.reply(f"An error occurred: `{e}`")
        return

    response_lines = [
        f"<b>Permissions for:</b> {target_user.mention}\n"
    ]

    status_map = {
        ChatMemberStatus.OWNER: "Owner",
        ChatMemberStatus.ADMINISTRATOR: "Administrator",
        ChatMemberStatus.MEMBER: "Member",
        ChatMemberStatus.RESTRICTED: "Restricted",
        ChatMemberStatus.LEFT: "Not in chat",
        ChatMemberStatus.BANNED: "Banned"
    }
    status_str = status_map.get(member.status, "Unknown Status")
    if member.custom_title: status_str += f"<i>({safe_escape(member.custom_title)})</i>"
    response_lines.append(f"• <b>Status:</b> {status_str}")
    
    if member.promoted_by:
        response_lines.append(f"• <b>Promoted By:</b> {member.promoted_by.mention}")

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
            perm_details = "\n".join([f"- {perm}" for perm in granted_perms])
            response_lines.append("• <b>Permissions:</b>")
            response_lines.append(f"<blockquote expandable>{perm_details}</blockquote>")
        else:
            response_lines.append("• <b>Permissions:</b> None")

    elif member.status == ChatMemberStatus.OWNER:
        response_lines.append("<b>Permissions:</b>")
        response_lines.append("<blockquote expandable>– All Permissions (Creator)</blockquote>")

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
            perm_details = "\n".join([f"- {perm}" for perm in denied_perms])
            response_lines.append("• <b>Restrictions:</b>")
            response_lines.append(f"<blockquote expandable>{perm_details}</blockquote>")
        
        if member.until_date:
            response_lines.append(f"<i>Restricted Until: {member.until_date.strftime('%d %b %Y, %H:%M UTC')}</i>")
        else:
            response_lines.append("<i>Restricted Until: Forever</i>")

    await message.reply(
        "\n".join(response_lines),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
