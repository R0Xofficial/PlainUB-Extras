import os
import html
import asyncio
from PIL import Image
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

TEMP_DIR = "temp_rotate/"
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

def sync_rotate_image(input_path: str, angle: int) -> str:
    """Synchronously rotates an image by a given angle."""
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_rotated{ext}")
    with Image.open(input_path) as img:
        rotated_img = img.rotate(-angle, expand=True)
        if rotated_img.mode in ("RGBA", "P"):
            rotated_img = rotated_img.convert("RGB")
        rotated_img.save(output_path)
    return output_path

async def sync_rotate_video_or_gif(input_path: str, rotations: int) -> str:
    """Synchronously rotates a video or GIF by applying the transpose filter N times."""
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_rotated{ext}")
    
    transpose_filter = ",".join(["transpose=1"] * rotations)
    
    command = (
        f'ffmpeg -i "{input_path}" '
        f'-vf "{transpose_filter}" '
        f'-c:a copy '
        f'-y "{output_path}"'
    )

    _, stderr, code = await run_command(command)
    if code != 0:
        raise RuntimeError(f"FFmpeg rotate failed: {stderr}")
        
    return output_path


@bot.add_cmd(cmd="rotate")
async def rotate_handler(bot: BOT, message: Message):
    """
    CMD: ROTATE
    INFO: Rotates the replied image, video, or GIF.
    USAGE:
        .rotate [times] (e.g., .rotate 2 for 180 degrees). Defaults to 1 (90 degrees).
    """
    replied_msg = message.replied
    is_media = replied_msg and (
        replied_msg.photo or replied_msg.video or replied_msg.animation or 
        (replied_msg.document and replied_msg.document.mime_type.startswith(("image/", "video/")))
    )
    if not is_media:
        return await message.reply("Please reply to an image, video, or GIF to rotate it.", del_in=MEDIUM_TIMEOUT)

    try:
        rotations = 1
        if message.input:
            rotations = int(message.input.strip())
        if not (1 <= rotations <= 3):
            raise ValueError("Number of rotations must be 1, 2, or 3.")
    except ValueError:
        return await message.reply("Invalid input. Please provide a number between 1 and 3.", del_in=MEDIUM_TIMEOUT)

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, modified_path = "", ""
    temp_files = []
    try:
        original_path = await bot.download_media(replied_msg)
        temp_files.append(original_path)
        
        angle = rotations * 90
        await progress_message.edit(f"<code>Rotating by {angle} degrees...</code>")
        
        is_image = replied_msg.photo or (replied_msg.document and replied_msg.document.mime_type.startswith('image/'))
        
        if is_image:
            modified_path = await asyncio.to_thread(sync_rotate_image, original_path, angle)
        else:
            modified_path = await sync_rotate_video_or_gif(original_path, rotations)
            
        temp_files.append(modified_path)
        
        await progress_message.edit("<code>Sending media...</code>")

        caption = f"Rotated by: `{angle}°`"
        reply_params = ReplyParameters(message_id=replied_msg.id)

        if is_image:
            await bot.send_photo(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        elif replied_msg.animation:
            await bot.send_animation(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        else:
            await bot.send_video(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not rotate media.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=LONG_TIMEOUT)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
