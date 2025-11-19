import os
import html
import asyncio
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

TEMP_DIR = "temp_reverse/"
os.makedirs(TEMP_DIR, exist_ok=True)

async def run_command(command: str) -> tuple[str, str, int]:
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode('utf-8', 'replace').strip(),
        stderr.decode('utf-8', 'replace').strip(),
        process.returncode
    )

async def sync_reverse_media(input_path: str, is_visual: bool) -> str:
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_reversed{ext}")
    
    command = ""
    if is_visual:
        command = f'ffmpeg -i "{input_path}" -vf "reverse" -af "areverse" -y "{output_path}"'
    else:
        command = f'ffmpeg -i "{input_path}" -af "areverse" -y "{output_path}"'

    _, stderr, code = await run_command(command)
    
    if code != 0:
        if is_visual and ("Cannot find a matching stream" in stderr or "anull" in stderr):
            command = f'ffmpeg -i "{input_path}" -vf "reverse" -an -y "{output_path}"'
            _, stderr_fallback, code_fallback = await run_command(command)
            if code_fallback != 0: raise RuntimeError(f"FFmpeg reverse failed (no audio): {stderr_fallback}")
        else:
            raise RuntimeError(f"FFmpeg reverse failed: {stderr}")
        
    return output_path

@bot.add_cmd(cmd="reverse")
async def reverse_handler(bot: BOT, message: Message):
    """
    CMD: REVERSE
    INFO: Reverses the replied video, GIF, or audio file.
    USAGE:
        .reverse
    """
    replied_msg = message.replied
    is_media = replied_msg and (
        replied_msg.video or replied_msg.animation or replied_msg.audio or replied_msg.voice or
        (replied_msg.document and replied_msg.document.mime_type.startswith(("video/", "audio/", "image/gif")))
    )
    if not is_media:
        return await message.reply("Please reply to a video, GIF, or audio file.", del_in=MEDIUM_TIMEOUT)

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, modified_path = "", ""
    temp_files = []
    try:
        media_object = (replied_msg.video or replied_msg.animation or replied_msg.audio or replied_msg.voice or replied_msg.document)
        original_path = await bot.download_media(media_object)
        temp_files.append(original_path)
        
        is_visual = bool(
            replied_msg.video or replied_msg.animation or
            (replied_msg.document and replied_msg.document.mime_type.startswith('video/')) or
            (replied_msg.document and replied_msg.document.mime_type == 'image/gif')
        )
        
        await progress_message.edit("<code>Reversing...</code>")
        
        modified_path = await sync_reverse_media(original_path, is_visual)
        temp_files.append(modified_path)
        
        await progress_message.edit("<code>Sending media...</code>")

        caption = "Reversed!"
        reply_params = ReplyParameters(message_id=replied_msg.id)
        
        is_animation = bool(replied_msg.animation or (replied_msg.document and replied_msg.document.mime_type == 'image/gif'))
        is_video = bool(replied_msg.video or (replied_msg.document and replied_msg.document.mime_type.startswith('video/')))

        if is_animation:
            await bot.send_animation(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        elif is_video:
            await bot.send_video(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        elif replied_msg.voice:
             await bot.send_voice(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        else:
            await bot.send_audio(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not reverse media.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=LONG_TIMEOUT)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
