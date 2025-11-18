import os
import html
import asyncio
import re
from PIL import Image
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_crop/"
os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_VISIBLE_DURATION = 8

async def run_command(command: str) -> tuple[str, str, int]:
    process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    return (stdout.decode('utf-8', 'replace').strip(), stderr.decode('utf-8', 'replace').strip(), process.returncode)

def sync_crop_image(input_path: str, width: int, height: int) -> str:
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_cropped{ext}")
    with Image.open(input_path) as img:
        orig_width, orig_height = img.size
        if width > orig_width or height > orig_height:
            raise ValueError(f"Crop dimensions ({width}x{height}) cannot be larger than the original image.")
        left = (orig_width - width) / 2
        top = (orig_height - height) / 2
        right = left + width
        bottom = top + height
        cropped_img = img.crop((left, top, right, bottom))
        if cropped_img.mode in ("RGBA", "P"): cropped_img = cropped_img.convert("RGB")
        cropped_img.save(output_path)
    return output_path

async def sync_crop_video(input_path: str, width: int, height: int) -> str:
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_cropped{ext}")
    crop_filter = f"crop={width}:{height}:(in_w-{width})/2:(in_h-{height})/2"
    command = f'ffmpeg -i "{input_path}" -vf "{crop_filter}" -c:a copy -y "{output_path}"'
    _, stderr, code = await run_command(command)
    if code != 0: raise RuntimeError(f"FFmpeg crop failed: {stderr}")
    return output_path

@bot.add_cmd(cmd="crop")
async def crop_handler(bot: BOT, message: Message):
    """
    CMD: CROP
    INFO: Crops the replied image from the center to specified dimensions.
    USAGE:
        .crop [width]x[height] (e.g., .crop 1280x720)
    """
    replied_msg = message.replied
    is_media = replied_msg and (replied_msg.photo or replied_msg.video or (replied_msg.document and replied_msg.document.mime_type.startswith(("image/", "video/"))))
    is_animation = replied_msg and (replied_msg.animation or (replied_msg.document and replied_msg.document.mime_type == 'image/gif'))
    
    if is_animation:
        return await message.reply("GIFs are not supported by this tool.", del_in=ERROR_VISIBLE_DURATION)
    if not is_media:
        return await message.reply("Please reply to an image or video to crop it.", del_in=ERROR_VISIBLE_DURATION)
        
    if not message.input:
        return await message.reply("<b>Usage:</b> .crop [width]x[height]", del_in=ERROR_VISIBLE_DURATION)
    
    match = re.match(r"(\d+)[x:](\d+)", message.input)
    if not match:
        return await message.reply("Invalid format. Use `.crop [width]x[height]`.", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, modified_path = "", ""
    temp_files = []
    try:
        media_object = (replied_msg.photo or replied_msg.video or replied_msg.document)
        original_path = await bot.download_media(media_object)
        temp_files.append(original_path)

        crop_width = int(match.group(1))
        crop_height = int(match.group(2))
        
        await progress_message.edit(f"<code>Cropping to {crop_width}x{crop_height}...</code>")
        
        is_image = replied_msg.photo or (replied_msg.document and replied_msg.document.mime_type.startswith('image/'))
        
        if is_image:
            modified_path = await asyncio.to_thread(sync_crop_image, original_path, crop_width, crop_height)
        else:
            modified_path = await sync_crop_video(original_path, crop_width, crop_height)

        temp_files.append(modified_path)
        
        await progress_message.edit("<code>Sending media...</code>")
        
        caption = f"Cropped to: `{crop_width}x{crop_height}`"
        reply_params = ReplyParameters(message_id=replied_msg.id)
        
        if is_image:
            await bot.send_photo(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        else:
            await bot.send_video(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not crop media.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
