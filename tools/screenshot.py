import os
import html
import asyncio
import requests
import time
import base64
from pyrogram.types import Message, ReplyParameters
from dotenv import load_dotenv

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(MODULES_DIR, "extra_config.env")
load_dotenv(dotenv_path=ENV_PATH)

PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY")

TEMP_DIR = "temp_screenshots/"
os.makedirs(TEMP_DIR, exist_ok=True)


@bot.add_cmd(cmd=["screenshot", "ss"])
async def screenshot_handler(bot: BOT, message: Message):
    if not PAGESPEED_API_KEY:
        await message.reply(
            "<b>PAGESPEED_API_KEY is not configured in extra_config.env.</b>",
            del_in=LONG_TIMEOUT
        )
        return

    if not message.input:
        await message.reply("<b>Usage:</b> .screenshot [url]", del_in=MEDIUM_TIMEOUT)
        return

    url = message.input.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    progress_msg = await message.reply(f"<code>Taking screenshot</code>...")
    
    output_path = os.path.join(TEMP_DIR, f"screenshot_{int(time.time())}.jpeg")

    try:
        api_endpoint = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?screenshot=true&strategy=desktop&url={url}&key={PAGESPEED_API_KEY}"

        def do_request():
            return requests.get(api_endpoint, timeout=60)

        response = await asyncio.to_thread(do_request)
        response.raise_for_status()

        result = response.json()
        
        screenshot_data = result.get("lighthouseResult", {}).get("audits", {}).get("final-screenshot", {}).get("details", {}).get("data")
        
        if not screenshot_data:
            raise ValueError("Google API did not return a screenshot for this URL.")

        image_data = base64.b64decode(screenshot_data.replace("data:image/jpeg;base64,", ""))

        with open(output_path, "wb") as f:
            f.write(image_data)
        
        if os.path.exists(output_path):
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=output_path,
                caption=f"Screenshot of: <code>{html.escape(url)}</code>",
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            await progress_msg.delete()
        else:
            raise FileNotFoundError("Screenshot file was not created.")

    except requests.exceptions.HTTPError as e:
        error_message = f"<b>API Error ({e.response.status_code}):</b>\n<code>{html.escape(e.response.text)}</code>"
        await progress_msg.edit(error_message, del_in=LONG_TIMEOUT)
        
    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
