import html
from pyrogram.types import Message, User
from pyrogram.enums import ChatType
from pyrogram.errors import UserNotParticipant

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

async def get_target_user(bot: BOT, message: Message) -> User | None:
    """Helper function to find the target user."""
    if message.replied:
        return message.replied.from_user
    if message.input:
        try:
            return await bot.get_users(message.input)
        except Exception:
            return None
    return message.from_user

@bot.add_cmd(cmd=["joininfo", "joindate"])
async def join_date_handler(bot: BOT, message: Message):
    """
    CMD: JOININFO / JOINDATE
    INFO: Shows when a user joined the current chat.
    USAGE:
        .joininfo (shows your join date)
        .joininfo [reply/id/username]
    """
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("This command can only be used in groups.", del_in=MEDIUM_TIMEOUT)
        return

    target_user = await get_target_user(bot, message)
    if not target_user:
        await message.reply("Could not find the specified user.", del_in=MEDIUM_TIMEOUT)
        return
        
    try:
        member = await bot.get_chat_member(message.chat.id, target_user.id)
        
        if member.joined_date:
            join_date_str = member.joined_date.strftime('%d %b %Y, %H:%M UTC')
            response = f"{target_user.mention} joined this chat on:\n<code>{join_date_str}</code>"
        else:
            response = f"Could not retrieve a specific join date for {target_user.mention}."

        await message.reply(response)

    except UserNotParticipant:
        await message.reply(f"User {target_user.mention} is not a member of this chat.")
    except Exception as e:
        await message.reply(f"<b>Error:</b> <code>{e}</code>", del_in=LONG_TIMEOUT)
