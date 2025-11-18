import os
import html
import asyncio
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_filecreator/"
os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_VISIBLE_DURATION = 8

def sync_create_file(filename: str, content: str) -> str:
    """Synchronously creates a file with the given content in the temp directory."""
    if ".." in filename or "/" in filename:
        raise ValueError("Invalid filename. It cannot contain '..' or '/'.")
        
    output_path = os.path.join(TEMP_DIR, filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return output_path


@bot.add_cmd(cmd="filecreate")
async def filecreator_handler(bot: BOT, message: Message):
    """
    CMD: FILECREATE
    INFO: Creates a file with the specified name and content.
    USAGE:
        .filecreate [filename.ext] (content)
        .filecreate [filename.ext] (in reply to a message)
    """
    replied_msg = message.replied
    
    if not message.input:
        return await message.reply(
            "<b>Usage:</b> .filecreate [filename.ext] (content)",
            del_in=ERROR_VISIBLE_DURATION
        )

    parts = message.input.split(maxsplit=1)
    filename = parts[0]
    
    content_to_write = ""
    reply_target = message

    if len(parts) > 1:
        content_to_write = parts[1]
    elif replied_msg and replied_msg.text:
        content_to_write = replied_msg.text
        reply_target = replied_msg
    else:
        return await message.reply("Please provide content directly or by replying to a text message.", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply("<code>Creating file...</code>")
    
    output_path = ""
    temp_files = []
    try:
        output_path = await asyncio.to_thread(sync_create_file, filename, content_to_write)
        temp_files.append(output_path)
        
        await progress_message.edit("<code>Sending file...</code>")

        await bot.send_document(
            chat_id=message.chat.id,
            document=output_path,
            caption=f"<code>{html.escape(filename)}</code>",
            reply_parameters=ReplyParameters(message_id=reply_target.id)
        )
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not create file.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
