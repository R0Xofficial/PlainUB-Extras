import os
import html
import uuid
import asyncio
import requests
from pyrogram.types import Message, ReplyParameters
from dotenv import load_dotenv
from PIL import Image

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(MODULES_DIR, "extra_config.env")
load_dotenv(dotenv_path=ENV_PATH)

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
MODEL = os.getenv("IMAGE_AI")

UBOT_DIR = os.path.dirname(os.path.dirname(MODULES_DIR)) 
LOGO_PATH = os.path.join(UBOT_DIR, "assets", "light.png")

TEMP_DIR = "temp_imagine/"
os.makedirs(TEMP_DIR, exist_ok=True)

def sync_add_watermark(image_path: str) -> str:
    """Opens an image from a file, adds a watermark, and saves it to a new file."""
    
    base, ext = os.path.splitext(os.path.basename(image_path))
    output_path = os.path.join(TEMP_DIR, f"{base}_wm.png")

    main_image = Image.open(image_path).convert("RGBA")
    
    if not os.path.exists(LOGO_PATH):
        main_image.save(output_path, "PNG")
        return output_path
        
    logo = Image.open(LOGO_PATH).convert("RGBA")
    
    main_width, main_height = main_image.size
    logo_width = main_width // 8
    logo_ratio = logo.height / logo.width
    new_logo_height = int(logo_width * logo_ratio)
    
    resized_logo = logo.resize((logo_width, new_logo_height), Image.Resampling.LANCZOS)
    
    padding = 0
    position = (main_width - resized_logo.width - padding, main_height - resized_logo.height - padding)
    
    main_image.paste(resized_logo, position, resized_logo)
    
    main_image.save(output_path, "PNG")
    
    return output_path

@bot.add_cmd(cmd=["image", "gen"])
async def imagine_handler(bot: BOT, message: Message):
    """
    CMD: IMAGE / GEN
    INFO: Generates an image from a text prompt (BETA).
    USAGE:
        .image [text prompt]
        .gen [text prompt]
    """
    if not MODEL or MODEL.strip() == "":
        return await message.reply("<b>Cloudflare Image Model AI not configured.</b>", del_in=LONG_TIMEOUT)
    
    if not CF_ACCOUNT_ID or not CF_API_TOKEN or "YOUR_KEY" in CF_API_TOKEN:
        return await message.reply("<b>Cloudflare API or Account ID not configured.</b>", del_in=LONG_TIMEOUT)

    if not message.input:
        return await message.reply("Please provide a text prompt.", del_in=MEDIUM_TIMEOUT)

    prompt = message.input
    progress_message = await message.reply("<code>Generating...</code>")
    
    generated_path, watermarked_path = "", ""
    temp_files = []
    try:
        api_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
        payload = {"prompt": prompt}
        
        response = await asyncio.to_thread(requests.post, api_url, headers=headers, json=payload)

        if response.ok:
            unique_id = str(uuid.uuid4())
            generated_path = os.path.join(TEMP_DIR, f"{unique_id}.png")
            with open(generated_path, "wb") as f:
                f.write(response.content)
            temp_files.append(generated_path)
            
            # watermarked_path = await asyncio.to_thread(sync_add_watermark, generated_path)
            # temp_files.append(watermarked_path)
            
            await bot.send_photo(
                chat_id=message.chat.id,
                # photo=watermarked_path,
                photo=generated_path,
                caption=f"<b>Prompt:</b> <i>{html.escape(prompt)}</i>",
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            await progress_message.delete()
        else:
            error_details = response.json()
            await progress_message.edit(f"API Error: {error_details}", del_in=LONG_TIMEOUT)

    except Exception as e:
        error_text = f"<b>Error:</b> Could not generate image.\n<code>{html.escape(str(e))}</code>"
        await progress_message.reply(error_text, del_in=LONG_TIMEOUT)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
