import os
import html
import asyncio
from PIL import Image
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_resize/"
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

def sync_resize_image(input_path: str, width: int, height: int) -> str:
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_resized{ext}")
    with Image.open(input_path) as img:
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
        if resized_img.mode in ("RGBA", "P"): resized_img = resized_img.convert("RGB")
        resized_img.save(output_path)
    return output_path

async def sync_resize_video_or_gif(input_path: str, width: int, height: int) -> tuple[str, str | None]:
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_resized{ext}")
    thumb_path = os.path.join(TEMP_DIR, f"{base}_thumb.jpg")
    
    command_resize = (
        f'ffmpeg -i "{input_path}" '
        f'-vf "scale={width}:{height},setsar=1" '
        f'-c:v libx264 -preset veryfast '
        f'-c:a aac '
        f'-y "{output_path}"'
    )
    _, stderr, code = await run_command(command_resize)
    if code != 0: raise RuntimeError(f"FFmpeg resize failed: {stderr}")
    
    command_thumb = f'ffmpeg -i "{output_path}" -ss 00:00:01 -vframes 1 -y "{thumb_path}"'
    _, stderr, code = await run_command(command_thumb)
    thumb_path = thumb_path if code == 0 else None
        
    return output_path, thumb_path


@bot.add_cmd(cmd="resize")
async def resize_handler(bot: BOT, message: Message):
    replied_msg = message.replied
    is_media = replied_msg and (replied_msg.photo or replied_msg.video or replied_msg.animation or (replied_msg.document and replied_msg.document.mime_type.startswith(("image/", "video/"))))
    if not is_media:
        return await message.reply("Please reply to an image, GIF, or video to resize it.", del_in=ERROR_VISIBLE_DURATION)

    if not message.input:
        await message.reply("Please specify the new resolution. Usage: `.resize 1920x1080`", del_in=ERROR_VISIBLE_DURATION)
        return

    try:
        width_str, height_str = message.input.lower().split('x')
        width, height = int(width_str), int(height_str)
        if not (0 < width <= 8192 and 0 < height <= 8192):
            raise ValueError("Dimensions must be between 1 and 8192.")
    except (ValueError, IndexError):
        await message.reply("Invalid resolution format. Please use `[width]x[height]`.", del_in=ERROR_VISIBLE_DURATION)
        return

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, resized_path, thumb_path = "", "", None
    temp_files = []
    try:
        original_path = await bot.download_media(replied_msg, file_name=TEMP_DIR)
        temp_files.append(original_path)
        
        await progress_message.edit(f"<code>Resizing to {width}x{height}...</code>")

        is_image = replied_msg.photo or (replied_msg.document and replied_msg.document.mime_type.startswith("image/"))
        is_video = replied_msg.video or (replied_msg.document and replied_msg.document.mime_type.startswith("video/"))
        is_animation = replied_msg.animation

        if is_image:
            resized_path = await asyncio.to_thread(sync_resize_image, original_path, width, height)
            temp_files.append(resized_path)
            await progress_message.edit("<code>Sending media...</code>")
            await bot.send_photo(
                message.chat.id,
                resized_path,
                caption=f"Resized to: `{width}x{height}`",
                reply_parameters=ReplyParameters(message_id=replied_msg.id)
            )
        
        elif is_video or is_animation:
            resized_path, thumb_path = await sync_resize_video_or_gif(original_path, width, height)
            temp_files.extend([resized_path, thumb_path] if thumb_path else [resized_path])

            await progress_message.edit("<code>Sending media...</code>")
            if is_video:
                await bot.send_video(
                    message.chat.id,
                    resized_path, 
                    caption=f"Resized to: `{width}x{height}`",
                    width=width,
                    height=height,
                    thumb=thumb_path,
                    reply_parameters=ReplyParameters(message_id=replied_msg.id)
                )
            else:
                await bot.send_animation(
                    message.chat.id,
                    resized_path, 
                    caption=f"Resized to: `{width}x{height}`",
                    width=width,
                    height=height,
                    thumb=thumb_path,
                    reply_parameters=ReplyParameters(message_id=replied_msg.id)
                )
        else:
            raise ValueError("Unsupported media type.")
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not resize media.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f): os.remove(f)
