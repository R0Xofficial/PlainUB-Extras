import html
from pyrogram.types import Message, User, Chat, ReplyParameters

from app import BOT, bot

ERROR_VISIBLE_DURATION = 8

@bot.add_cmd(cmd="pfp")
async def pfp_handler(bot: BOT, message: Message):
    """
    CMD: PFP
    INFO: Fetches the current profile picture of a user, group, or channel.
    USAGE:
        .pfp (on yourself)
        .pfp [user_id/username/chat_id]
        .pfp (in reply to a user)
    """
    target_entity: User | Chat = None
    target_id = None
    
    try:
        if message.input:
            identifier = message.input.strip()
            try:
                target_entity = await bot.get_users(identifier)
            except Exception:
                target_entity = await bot.get_chat(identifier)

        elif message.replied:
            if message.replied.from_user:
                target_entity = message.replied.from_user
            else:
                target_entity = message.replied.sender_chat

        else:
            target_entity = message.from_user
            
        if not target_entity:
            raise ValueError("Could not identify the target.")

        target_id = target_entity.id
        
        if isinstance(target_entity, User):
            target_name = target_entity.first_name
        else:
            target_name = target_entity.title
        
        if not target_name:
            target_name = "their"
            
    except Exception as e:
        return await message.reply(f"Could not find the specified user or chat.\n<code>{html.escape(str(e))}</code>", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply(f"<code>Fetching {html.escape(target_name)}'s profile photo...</code>")

    try:
        media_sent = False
        async for photo in bot.get_chat_photos(target_id, limit=1):
            
            if isinstance(target_entity, User):
                caption_text = f"{target_entity.mention}'s profile photo."
            else:
                caption_text = f"Profile photo of <b>{html.escape(target_entity.title)}</b>."
            
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=photo.file_id,
                caption=caption_text,
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            
            media_sent = True
            break
        
        if not media_sent:
            return await progress_message.edit("This entity has no profile photo.", del_in=ERROR_VISIBLE_DURATION)

        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not fetch profile photo.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
