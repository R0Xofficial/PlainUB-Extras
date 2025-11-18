import os
import html
import asyncio
from PIL import Image
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_upscale/"
os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_VISIBLE_DURATION = 8

async def run_command(command: str) -> tuple[str, str, int]:
    process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return (stdout.decode('utf-8', 'replace').strip(), stderr.decode('utf-8', 'replace').strip(), process.returncode)

def sync_upscale_image(input_path: str, scale_factor: int = 2) -> tuple[str, int, int]:
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_upscaled{ext}")
    with Image.open(input_path) as img:
        orig_width, orig_height = img.size
        new_width = orig_width * scale_factor
        new_height = orig_height * scale_factor
        upscaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        if upscaled_img.mode in ("RGBA", "P"): upscaled_img = upscaled_img.convert("RGB")
        upscaled_img.save(output_path)
    return output_path, new_width, new_height

async def sync_upscale_video(input_path: str, scale_factor: int = 2) -> tuple[str, int, int]:
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_upscaled{ext}")
    
    probe_command = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "{input_path}"'
    stdout, _, _ = await run_command(probe_command)
    orig_width, orig_height = map(int, stdout.split('x'))
    new_width = orig_width * scale_factor
    new_height = orig_height * scale_factor
    
    scale_filter = f"scale=iw*{scale_factor}:ih*{scale_factor}:flags=lanczos"
    command = f'ffmpeg -i "{input_path}" -vf "{scale_filter}" -c:a copy -y "{output_path}"'
    _, stderr, code = await run_command(command)
    if code != 0: raise RuntimeError(f"FFmpeg upscale failed: {stderr}")
        
    return output_path, new_width, new_height

@bot.add_cmd(cmd="upscale")
async def upscale_handler(bot: BOT, message: Message):
    """
    CMD: UPSCALE
    INFO: Upscales the replied image to 2x its original size.
    USAGE:
        .upscale
    """
    replied_msg = message.replied
    is_media = replied_msg and (
        replied_msg.photo or replied_msg.video or
        (replied_msg.document and replied_msg.document.mime_type.startswith(("image/", "video/")))
    )
    is_animation = replied_msg and (replied_msg.animation or (replied_msg.document and replied_msg.document.mime_type == 'image/gif'))

    if is_animation:
        return await message.reply("GIFs are not supported by this tool.", del_in=ERROR_VISIBLE_DURATION)
    if not is_media:
        return await message.reply("Please reply to an image or video to upscale it.", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, modified_path = "", ""
    temp_files = []
    try:
        media_object = (replied_msg.photo or replied_msg.video or replied_msg.document)
        original_path = await bot.download_media(media_object)
        temp_files.append(original_path)
        
        await progress_message.edit("<code>Upscaling...</code>")
        
        is_image = replied_msg.photo or (replied_msg.document and replied_msg.document.mime_type.startswith('image/'))
        
        if is_image:
            modified_path, new_width, new_height = await asyncio.to_thread(sync_upscale_image, original_path)
        else:
            modified_path, new_width, new_height = await sync_upscale_video(original_path)
        
        temp_files.append(modified_path)
        
        await progress_message.edit("<code>Sending media...</code>")
        
        caption = f"Upscaled to: `{new_width}x{new_height}`"
        reply_params = ReplyParameters(message_id=replied_msg.id)
        
        if is_image:
            await bot.send_photo(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        else:
            await bot.send_video(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not upscale media.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
