import os
import html
import asyncio
import shutil
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_extract_audio/"
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


@bot.add_cmd(cmd=["getaudio", "geta"])
async def extract_audio_handler(bot: BOT, message: Message):
    """
    CMD: GETAUDIO
    INFO: Extracts the audio track from a replied-to video file.
    USAGE:
        .getaudio (in reply to a video)
    ALIASES: .geta
    """
    replied_msg = message.replied
    
    is_video = replied_msg and (
        replied_msg.video or 
        (replied_msg.document and replied_msg.document.mime_type.startswith("video/"))
    )
    
    if not is_video:
        await message.reply("Please reply to a video to extract its audio.", del_in=8)
        return

    progress_msg = await message.reply("<code>Downloading video...</code>")
    
    video_path = None
    audio_path = None
    try:
        video_path = await bot.download_media(replied_msg, file_name=TEMP_DIR)
        
        await progress_msg.edit("<code>Extracting audio track...</code>")
        
        base, _ = os.path.splitext(os.path.basename(video_path))
        audio_path = os.path.join(TEMP_DIR, f"{base}.mp3")
        
        command = f'ffmpeg -i "{video_path}" -vn -acodec copy -y "{audio_path}"'
        _, stderr, returncode = await run_command(command)

        if returncode != 0:
            command = f'ffmpeg -i "{video_path}" -vn -c:a libmp3lame -q:a 2 -y "{audio_path}"'
            _, stderr, returncode = await run_command(command)
            if returncode != 0:
                raise RuntimeError(f"FFmpeg failed to extract audio: {stderr}")

        if not os.path.exists(audio_path):
            raise FileNotFoundError("Audio file was not created.")

        await progress_msg.edit("<code>Uploading audio...</code>")

        await bot.send_audio(
            chat_id=message.chat.id,
            audio=audio_path,
            reply_parameters = ReplyParameters(message_id=replied_msg.id)
        )
        
        await progress_msg.delete()

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=10)
    finally:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
