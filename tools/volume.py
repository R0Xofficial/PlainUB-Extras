import os
import html
import asyncio
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_volume/"
os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_VISIBLE_DURATION = 8

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

async def sync_change_volume(input_path: str, volume_factor: float) -> str:
    """Synchronously changes the volume of a media file using FFmpeg."""
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_volume_{int(volume_factor*100)}.mp3")
    
    command = (
        f'ffmpeg -i "{input_path}" '
        f'-af "aformat=sample_fmts=s16:sample_rates=44100,volume={volume_factor}" '
        f'-c:a libmp3lame -b:a 192k '
        f'-c:v copy '
        f'-y "{output_path}"'
    )

    _, stderr, code = await run_command(command)
    if code != 0:
        if "does not contain any stream" in stderr or "Invalid argument" in stderr:
            command = (
                f'ffmpeg -i "{input_path}" '
                f'-af "volume={volume_factor}" '
                f'-c:a libmp3lame -b:a 192k '
                f'-vn '
                f'-y "{output_path}"'
            )
            _, stderr_fallback, code_fallback = await run_command(command)
            if code_fallback != 0: raise RuntimeError(f"FFmpeg volume change failed: {stderr_fallback}")
        else:
            raise RuntimeError(f"FFmpeg volume change failed: {stderr}")
        
    return output_path


@bot.add_cmd(cmd=["volume", "vol"])
async def volume_handler(bot: BOT, message: Message):
    """
    CMD: VOLUME / VOL
    INFO: Changes the volume of the replied media file. 100 is the original volume.
    USAGE:
        .volume [level] (e.g., .volume 200 for 2x volume, .volume 50 for half volume)
    """
    replied_msg = message.replied
    is_media = replied_msg and (
        replied_msg.video or replied_msg.audio or replied_msg.voice or
        (replied_msg.document and replied_msg.document.mime_type.startswith(("video/", "audio/")))
    )
    if not is_media:
        return await message.reply("Please reply to a video or audio file.", del_in=ERROR_VISIBLE_DURATION)

    if not message.input:
        return await message.reply("Please specify a volume level (100 = original). Usage: `.volume 150`", del_in=ERROR_VISIBLE_DURATION)

    try:
        volume_level = float(message.input.strip())
        if volume_level < 0:
            raise ValueError("Volume level cannot be negative.")
        
        volume_factor = volume_level / 100.0
    except ValueError:
        return await message.reply("Invalid input. Please use a number like `200` or `50`.", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, modified_path = "", ""
    temp_files = []
    try:
        media_object = (replied_msg.video or replied_msg.audio or replied_msg.voice or replied_msg.document)
        original_path = await bot.download_media(media_object)
        temp_files.append(original_path)
        
        await progress_message.edit(f"<code>Changing volume to level {int(volume_level)}...</code>")
        
        modified_path = await sync_change_volume(original_path, volume_factor)
        temp_files.append(modified_path)
        
        await progress_message.edit("<code>Sending media...</code>")

        caption = f"Volume set to: `{int(volume_level)}`"
        reply_params = ReplyParameters(message_id=replied_msg.id)

        is_video = replied_msg.video or (replied_msg.document and replied_msg.document.mime_type.startswith('video/'))

        if is_video:
            await bot.send_video(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        elif replied_msg.voice:
             await bot.send_voice(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        else:
            await bot.send_audio(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not change volume.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
