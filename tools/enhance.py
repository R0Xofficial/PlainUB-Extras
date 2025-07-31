import os
import html
import asyncio
from PIL import Image, ImageEnhance, ImageFilter
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_enhance/"
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

def sync_enhance_image(input_path: str) -> tuple[str, int, int]:
    """Synchronously upscales and enhances a static image."""
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_enhanced.png")
    with Image.open(input_path) as img:
        if img.mode not in ("RGB", "RGBA"): img = img.convert("RGBA")
        orig_width, orig_height = img.size
        new_width, new_height = orig_width * 2, orig_height * 2
        upscaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        enhancer_sharp = ImageEnhance.Sharpness(upscaled_img)
        sharpened_img = enhancer_sharp.enhance(2.0)
        smoothed_img = sharpened_img.filter(ImageFilter.SMOOTH)
        enhancer_contrast = ImageEnhance.Contrast(smoothed_img)
        final_image = enhancer_contrast.enhance(1.2)
        final_image.save(output_path, "PNG")
    return output_path, new_width, new_height

async def sync_enhance_video_or_gif(input_path: str) -> tuple[str, int, int]:
    """Synchronously upscales and enhances a video or GIF using FFmpeg."""
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_enhanced{ext}")
    
    probe_command = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "{input_path}"'
    stdout, _, _ = await run_command(probe_command)
    orig_width, orig_height = map(int, stdout.split('x'))
    new_width, new_height = orig_width * 2, orig_height * 2

    # A complex filter chain: upscale, then sharpen, then denoise
    filter_chain = (
        f"scale={new_width}:{new_height}:flags=lanczos,"
        f"unsharp=5:5:1.0:5:5:0.0,"
        f"hqdn3d"
    )

    command = (
        f'ffmpeg -i "{input_path}" '
        f'-vf "{filter_chain}" '
        f'-c:a copy '
        f'-y "{output_path}"'
    )

    _, stderr, code = await run_command(command)
    if code != 0:
        raise RuntimeError(f"FFmpeg enhance failed: {stderr}")
        
    return output_path, new_width, new_height


@bot.add_cmd(cmd="enhance")
async def enhance_handler(bot: BOT, message: Message):
    """
    CMD: ENHANCE
    INFO: Upscales and enhances the quality of the replied image, video, or GIF.
    USAGE:
        .enhance
    """
    replied_msg = message.replied
    is_media = replied_msg and (
        replied_msg.photo or replied_msg.video or replied_msg.animation or
        (replied_msg.document and replied_msg.document.mime_type.startswith(("image/", "video/", "image/gif")))
    )
    if not is_media:
        return await message.edit("Please reply to an image, video, or GIF to enhance it.", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply("<code>Downloading media...</code>")
    
    original_path, modified_path = "", ""
    temp_files = []
    try:
        media_object = (replied_msg.photo or replied_msg.video or replied_msg.animation or replied_msg.document)
        original_path = await bot.download_media(media_object)
        temp_files.append(original_path)
        
        is_image = replied_msg.photo or (replied_msg.document and replied_msg.document.mime_type.startswith('image/') and not replied_msg.document.mime_type == 'image/gif')

        if is_image:
            await progress_message.edit("<code>Enhancing image quality...</code>")
            modified_path, new_width, new_height = await asyncio.to_thread(sync_enhance_image, original_path)
        else: # is_video or is_animation (GIF)
            await progress_message.edit("<code>Enhancing video quality... (this can be slow)</code>")
            modified_path, new_width, new_height = await sync_enhance_video_or_gif(original_path)
        
        temp_files.append(modified_path)
        
        await progress_message.edit("<code>Sending as file...</code>")
        
        caption = f"Enhanced to: `{new_width}x{new_height}`"
        reply_params = ReplyParameters(message_id=replied_msg.id)
        
        await bot.send_document(message.chat.id, modified_path, caption=caption, reply_parameters=reply_params)
        
        await progress_message.delete()
        await message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not enhance media.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
