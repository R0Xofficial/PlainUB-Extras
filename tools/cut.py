import os
import html
import asyncio
import shutil
from pyrogram.types import Message

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

TEMP_DIR = "temp_cut/"
os.makedirs(TEMP_DIR, exist_ok=True)

async def run_command(command: str) -> tuple[str, str, int]:
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode('utf-8', 'replace').strip(),
        stderr.decode('utf-8', 'replace').strip(),
        process.returncode
    )


@bot.add_cmd(cmd="cut")
async def cut_media_handler(bot: BOT, message: Message):
    """
    CMD: CUT
    INFO: Trims an audio or video file to the specified time range.
    USAGE:
        .cut [start]-[end] (in reply to media)
    EXAMPLE:
        .cut 0:15-0:45
        .cut 1:30-1:45
    """
    replied_msg = message.replied
    
    is_media = replied_msg and (
        replied_msg.video or replied_msg.audio or replied_msg.voice or
        (replied_msg.document and replied_msg.document.mime_type.startswith(("video/", "audio/")))
    )
    
    if not is_media:
        await message.reply("Please reply to a video or audio file to cut it.", del_in=MEDIUM_TIMEOUT)
        return

    if not message.input or "-" not in message.input:
        await message.reply("<b>Usage:</b> <code>.cut [start]-[end]</code> (e.g., <code>.cut 1:10-1:25</code>)", del_in=MEDIUM_TIMEOUT)
        return

    time_parts = message.input.split('-')
    if len(time_parts) != 2:
        await message.reply("<b>Invalid time format.</b> Please use `start-end`.", del_in=MEDIUM_TIMEOUT)
        return
        
    start_time, end_time = time_parts[0].strip(), time_parts[1].strip()

    progress_msg = await message.reply("<code>Downloading media...</code>")
    
    downloaded_path = None
    output_path = None
    try:
        downloaded_path = await bot.download_media(replied_msg, file_name=TEMP_DIR)
        
        await progress_msg.edit(f"<code>Trimming from {start_time} to {end_time}...</code>")
        
        base, ext = os.path.splitext(os.path.basename(downloaded_path))
        output_path = os.path.join(TEMP_DIR, f"{base}_cut{ext}")
        
        command = (
            f'ffmpeg -i "{downloaded_path}" '
            f'-ss {start_time} -to {end_time} '
            f'-c copy -y "{output_path}"'
        )

        _, stderr, returncode = await run_command(command)

        if returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise FileNotFoundError("Trimmed file was not created or is empty. Check time format.")

        await progress_msg.edit("<code>Uploading file...</code>")

        caption = f"Trimmed from <code>{start_time}</code> to <code>{end_time}</code>."
        
        is_video = replied_msg.video or (replied_msg.document and "video" in replied_msg.document.mime_type)
        if is_video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=output_path,
                caption=caption,
                reply_to_message_id=replied_msg.id
            )
        else:
            await bot.send_audio(
                chat_id=message.chat.id,
                audio=output_path,
                caption=caption,
                reply_to_message_id=replied_msg.id
            )
        
        await progress_msg.delete()

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
    finally:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
