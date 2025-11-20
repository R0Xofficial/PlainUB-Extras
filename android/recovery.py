import asyncio
import html
import aiohttp
from datetime import datetime
from pyrogram.types import Message, LinkPreviewOptions, InlineKeyboardMarkup, InlineKeyboardButton

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}

@bot.add_cmd(cmd="orangefox")
async def orangefox_handler(bot: BOT, message: Message):
    """
    CMD: ORANGEFOX
    INFO: Fetches the latest OrangeFox Recovery for a given device.
    USAGE: 
        .orangefox [codename]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.orangefox [codename]</code>", del_in=MEDIUM_TIMEOUT); return

    codename = message.input.lower()
    progress = await message.reply(f"<code>Searching for OrangeFox releases for {codename}...</code>")
    
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(f"https://api.orangefox.download/v3/releases/?codename={codename}&sort=date_desc&limit=1") as response:
                response.raise_for_status()
                data = await response.json()
                
                if not data.get("data"):
                    raise ValueError("No releases found for this device.")
                
                release = data["data"][0]

        file_id = release["_id"]
        
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(f"https://api.orangefox.download/v3/releases/get?_id={file_id}") as response:
                response.raise_for_status()
                details = await response.json()
        
        dl_link = details["mirrors"][next(iter(details["mirrors"]))]
        
        response_text = (
            f"🦊 <b>Latest OrangeFox for {html.escape(details.get('full_name', codename))}</b>\n\n"
            f"<b>Version:</b> <code>{html.escape(details.get('version', 'N/A'))} ({html.escape(details.get('type', 'N/A'))})</code>\n"
            f"<b>File:</b> <code>{html.escape(details.get('filename', 'N/A'))}</code>\n"
            f"<b>Size:</b> <code>{round(float(details.get('size', 0)) / 1024 / 1024, 2)} MB</code>\n"
            f"<b>Date:</b> <code>{datetime.fromtimestamp(details.get('date', 0)).strftime('%Y-%m-%d')}</code>\n"
            f"<b>MD5:</b> <code>{html.escape(details.get('md5', 'N/A'))}</code>"
        )
        
        buttons = [[InlineKeyboardButton("Download", url=dl_link)]]
        
        await progress.edit(response_text, reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        error_msg = f"<b>Error:</b> Could not fetch OrangeFox release for <code>{codename}</code>."
        if "No releases found" in str(e):
             error_msg = f"<b>Sorry:</b> No official OrangeFox release found for <code>{codename}</code>."
        await progress.edit(error_msg, del_in=LONG_TIMEOUT)


@bot.add_cmd(cmd="twrp")
async def twrp_handler(bot: BOT, message: Message):
    """
    CMD: TWRP
    INFO: Fetches the latest official TWRP for a given device.
    USAGE: 
        .twrp [codename]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.twrp [codename]</code>", del_in=MEDIUM_TIMEOUT); return
        
    codename = message.input.lower()
    progress = await message.reply(f"<code>Searching for TWRP releases for {codename}...</code>")
    
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(f"https://twrp.me/devices/data/{codename}.json") as response:
                if response.status != 200:
                    raise ValueError("Device not found on TWRP servers.")
                
                data = await response.json()
                
        if not data.get("downloads"):
            raise ValueError("No download links found for this device.")
            
        latest_download_path = data["downloads"][0]
        download_url = f"https://twrp.me{latest_download_path}"
        
        response_text = (
            f"📱 <b>Latest TWRP for {html.escape(data.get('pretty_name', codename))}</b>\n\n"
            f"<b>Maintainer:</b> <code>{html.escape(data.get('maintainer', 'N/A'))}</code>\n"
            f"<b>Version:</b> <code>{html.escape(data.get('version', 'N/A'))}</code>"
        )
        
        buttons = [[InlineKeyboardButton("Download Page", url=download_url)]]
        
        await progress.edit(response_text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        error_msg = f"<b>Error:</b> Could not fetch TWRP release for <code>{codename}</code>."
        if "Device not found" in str(e):
             error_msg = f"<b>Sorry:</b> No official TWRP release found for <code>{codename}</code>."
        await progress.edit(error_msg, del_in=LONG_TIMEOUT)
