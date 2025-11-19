import os
import html
import asyncio
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

TEMP_DIR = "temp_speed/"
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

async def sync_change_speed(input_path: str, speed_factor: float, is_video: bool) -> str:
    """Synchronously changes the speed of a media file using FFmpeg, handling a wide range of values."""
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_speed_{speed_factor}x{ext}")
    
    atempo_filters = []
    temp_factor = speed_factor
    while temp_factor > 100.0:
        atempo_filters.append("atempo=100.0")
        temp_factor /= 100.0
    while temp_factor < 0.5:
        atempo_filters.append("atempo=0.5")
        temp_factor /= 0.5
    atempo_filters.append(f"atempo={temp_factor}")
    
    audio_filter_str = ",".join(atempo_filters)

    command = ""
    if is_video:
        video_filter = f"[0:v]setpts={1/speed_factor}*PTS[v]"
        audio_filter = f"[0:a]{audio_filter_str}[a]"
        command = (
            f'ffmpeg -i "{input_path}" '
            f'-filter_complex "{video_filter};{audio_filter}" '
            f'-map "[v]" -map "[a]" '
            f'-y "{output_path}"'
        )
    else:
        command = (
            f'ffmpeg -i "{input_path}" '
            f'-filter:a "{audio_filter_str}" '
            f'-y "{output_path}"'
        )

    _, stderr, code = await run_command(command)
    
    if code != 0:
        if is_video and "Cannot find a matching stream" in stderr:
            command = (
                f'ffmpeg -i "{input_path}" '
                f'-filter:v "setpts={1/speed_factor}*PTS" -an '
                f'-y "{output_path}"'
            )
            _, stderr_fallback, code_fallback = await run_command(command)
            if code_fallback != 0: raise RuntimeError(f"FFmpeg failed (no audio): {stderr_fallback}")
        else:
            raise RuntimeError(f"FFmpeg failed: {stderr}")
        
    return output_path


@bot.add_cmd(cmd="speed")
async def speed_handler(bot: BOT, message: Message):
    """
    CMD: SPEED
    INFO: Speeds up or slows down the replied video/audio.
    USAGE:
        .speed [factor] (e.g., .speed 5 for 5x faster, .speed 0.5 for 2x slower)
    """
    replied_msg = message.replied
    is_media = replied_msg and (replied_msg.video or replied_msg.audio or replied_msg.voice or (replied_msg.document and replied_msg.document.mime_type.startswith(("video/", "audio/"))))
    if not is_media:
        return await message.reply("Please reply to a video or audio file.", del_in=MEDIUM_TIMEOUT)

    if not message.input:
        return await message.reply("Please specify a speed factor. Usage: `.speed 2.0`", del_in=MEDIUM_TIMEOUT)

    try:
        speed_factor = float(message.input.strip())
        if speed_factor <= 0:
            raise ValueError("Speed factor must be a positive number.")
    except ValueError:
        return await message.reply("Invalid speed factor. Please use a number like `5` or `0.5`.", del_in=MEDIUM_TIMEOUT)

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, modified_path = "", ""
    temp_files = []
    try:
        media_object = (replied_msg.video or replied_msg.audio or replied_msg.voice or replied_msg.document)
        original_path = await bot.download_media(media_object)
        temp_files.append(original_path)
        
        is_video = bool(replied_msg.video or (replied_msg.document and replied_msg.document.mime_type.startswith('video/')))
        
        await progress_message.edit(f"<code>Changing speed to {speed_factor}x...</code>")
        
        modified_path = await sync_change_speed(original_path, speed_factor, is_video)
        temp_files.append(modified_path)
        
        await progress_message.edit("<code>Sending media...</code>")

        caption = f"Speed changed to: `{speed_factor}x`"
        reply_params = ReplyParameters(message_id=replied_msg.id)

        if is_video:
            await bot.send_video(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        elif replied_msg.voice:
             await bot.send_voice(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        else:
            await bot.send_audio(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not change speed.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=LONG_TIMEOUT)
    finally:
        for f in temp_files:
            if f and os.path.exists(f): os.remove(f)
