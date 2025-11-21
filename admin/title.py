import html
from pyrogram.types import Message, User
from pyrogram.enums import ChatType, ChatMemberStatus

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

async def get_target_user(bot: BOT, message: Message) -> User | None:
    if message.replied:
        return message.replied.from_user
    if message.input:
        try:
            identifier = message.input.split(" ", 1)[0]
            return await bot.get_users(identifier)
        except Exception:
            return None
    return None

@bot.add_cmd(cmd="title")
async def set_admin_title_handler(bot: BOT, message: Message):
    """
    CMD: TITLE
    INFO: Sets or removes a custom title for an administrator.
    USAGE:
        .title [reply/id/username] [custom title]
        .title [reply/id/username] (to remove the title)
    """
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("This command can only be used in groups.", del_in=MEDIUM_TIMEOUT)
        return

    me_member = await bot.get_chat_member(message.chat.id, bot.me.id)
    if not me_member.privileges or not me_member.privileges.can_promote_members:
        await message.reply("I need to be an admin with 'Promote Members' rights to do this.", del_in=MEDIUM_TIMEOUT)
        return

    target_user = await get_target_user(bot, message)
    if not target_user:
        await message.reply("You need to specify a user (reply, ID, or username).", del_in=MEDIUM_TIMEOUT)
        return
        
    target_member = await bot.get_chat_member(message.chat.id, target_user.id)

    if target_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await message.reply("This user is not an administrator.", del_in=MEDIUM_TIMEOUT)
        return
        
    if target_member.status == ChatMemberStatus.OWNER:
        await message.reply("You cannot change the title of the group owner.", del_in=MEDIUM_TIMEOUT)
        return

    args = message.input.split(" ", 1)
    new_title = ""
    if len(args) > 1:
        new_title = args[1]
    
    try:
        await bot.set_administrator_title(
            chat_id=message.chat.id,
            user_id=target_user.id,
            title=new_title
        )
        
        if new_title:
            response = f"Successfully set title for {target_user.mention} to '<code>{html.escape(new_title)}</code>'."
        else:
            response = f"Successfully removed custom title from {target_user.mention}."
        
        await message.reply(response)

    except Exception as e:
        await message.reply(f"<b>Error:</b> Could not set title. <code>{e}</code>", del_in=LONG_TIMEOUT)
