import os
import html
import asyncio
import json
import io
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

def json_cleaner(o):
    """
    A custom serializer for json.dumps to handle Pyrogram objects.
    It converts objects to their dictionary representation and censors sensitive data.
    """
    if hasattr(o, '__dict__'):
        clean_dict = {}
        for key, value in o.__dict__.items():
            if not key.startswith('_'):
                clean_dict[key] = value
        
        # Censor the phone number before returning the dictionary
        if "phone_number" in clean_dict and clean_dict["phone_number"]:
            clean_dict["phone_number"] = "[CENSORED]"
            
        return clean_dict
    try:
        return str(o)
    except:
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


@bot.add_cmd(cmd=["dev", "json"])
async def dev_handler(bot: BOT, message: Message):
    """
    CMD: DEV / JSON
    INFO: Shows the raw Pyrogram message object as a JSON file.
    USAGE:
        .dev (shows info about the command message)
        .dev (in reply to a message, shows info about that message)
    """
    
    target_message = message.replied or message
    
    progress_message = await message.reply("<code>Serializing message object to JSON...</code>")
    
    try:
        message_data_str = json.dumps(
            target_message,
            indent=4,
            default=json_cleaner,
            ensure_ascii=False
        )
        
        with io.BytesIO(message_data_str.encode('utf-8')) as doc:
            doc.name = f"message_data_{target_message.id}.json"
            
            await progress_message.edit("<code>Sending data file...</code>")
            
            await bot.send_document(
                chat_id=message.chat.id,
                document=doc,
                caption=f"Raw JSON data for message ID: <code>{target_message.id}</code>",
                reply_parameters=ReplyParameters(message_id=target_message.id)
            )
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not process message.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=LONG_TIMEOUT)
