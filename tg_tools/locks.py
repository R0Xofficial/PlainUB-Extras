import html
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatType

from app import BOT, bot
from app.modules.settings import MEDIUM_TIMEOUT

LOCK_TYPES = {
    "msg": "can_send_messages",
    "media": "can_send_media_messages",
    "stickers": "can_send_other_messages",
    "polls": "can_send_polls",
    "links": "can_add_web_page_previews",
    "invite": "can_invite_users",
    "pin": "can_pin_messages",
    "info": "can_change_info",
}

ALL_LOCKS = list(LOCK_TYPES.keys())

UNLOCK_ALL_DEFAULTS = [
    "msg", "media", "stickers", "polls", "links", "invite"
]

async def change_lock(bot: BOT, message: Message, lock: bool):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("This command can only be used in groups.", del_in=MEDIUM_TIMEOUT)
        return

    member = await bot.get_chat_member(message.chat.id, bot.me.id)
    if not member.privileges or not member.privileges.can_restrict_members:
        await message.reply("I need admin rights to change chat permissions.", del_in=MEDIUM_TIMEOUT)
        return

    lock_type = message.input
    if not lock_type:
        await message.reply("You need to specify what to lock/unlock.", del_in=MEDIUM_TIMEOUT)
        return

    current_permissions = message.chat.permissions
    
    if lock_type.lower() == "all":
        if lock:
            types_to_change = ALL_LOCKS
        else:
            types_to_change = UNLOCK_ALL_DEFAULTS
    else:
        types_to_change = [t.strip() for t in lock_type.lower().split()]

    changed_perms = []
    not_found_perms = []

    new_permissions_dict = {
        p: getattr(current_permissions, p) 
        for p in dir(current_permissions) 
        if not p.startswith('_')
    }
    
    for t in types_to_change:
        if t in LOCK_TYPES:
            perm_attribute = LOCK_TYPES[t]
            new_permissions_dict[perm_attribute] = not lock
            changed_perms.append(t)
        else:
            not_found_perms.append(t)
            
    if not changed_perms:
        await message.reply(f"Invalid lock type(s): `{' '.join(not_found_perms)}`", del_in=MEDIUM_TIMEOUT)
        return

    new_permissions = ChatPermissions(**new_permissions_dict)

    try:
        await bot.set_chat_permissions(message.chat.id, new_permissions)
        action = "Locked" if lock else "Unlocked"
        response = f"<b>{action}:</b> `{' '.join(changed_perms)}`"
        if not_found_perms:
            response += f"\n<b>Not found:</b> `{' '.join(not_found_perms)}`"
        await message.reply(response, del_in=MEDIUM_TIMEOUT)
    except Exception as e:
        await message.reply(f"<b>Error:</b> Could not change permissions. <code>{e}</code>")


@bot.add_cmd(cmd="lock")
async def lock_handler(bot: BOT, message: Message):
    """
    CMD: LOCK
    INFO: Restricts users from performing certain actions in the chat.
    USAGE:
        .lock [type]
        .lock all
    """
    await change_lock(bot, message, lock=True)

@bot.add_cmd(cmd="unlock")
async def unlock_handler(bot: BOT, message: Message):
    """
    CMD: UNLOCK
    INFO: Allows users to perform actions that were previously locked.
    USAGE:
        .unlock [type]
        .unlock all
    """
    await change_lock(bot, message, lock=False)

@bot.add_cmd(cmd="locktypes")
async def locktypes_handler(bot: BOT, message: Message):
    """
    CMD: LOCKTYPES
    INFO: Shows a list of all available lock types.
    """
    response = "<b>Available Lock Types:</b>\n\n"
    for lock_name, perm_name in LOCK_TYPES.items():
        description = perm_name.replace("can_", "").replace("_", " ").title()
        response += f"• <code>{lock_name}</code> - {description}\n"
    response += "\nUse <code>all</code> to affect all types at once."
    await message.reply(response)
