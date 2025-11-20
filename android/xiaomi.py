import asyncio
import html
import aiohttp
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

DEVICES_JSON_URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/mi-firmware-updater/master/data/devices.json"
SPECS_API_URL = "https://api.rev-tech.me/v1/devices/details/"

DEVICE_DATA = []
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
}

async def load_device_data():
    global DEVICE_DATA
    if DEVICE_DATA:
        return
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(DEVICES_JSON_URL) as response:
                response.raise_for_status()
                DEVICE_DATA = await response.json()
    except Exception:
        DEVICE_DATA = None

def safe_escape(text: str) -> str:
    return html.escape(str(text))

async def find_device(query: str):
    if not DEVICE_DATA:
        await load_device_data()
    if DEVICE_DATA is None:
        return None
    
    query = query.lower()
    for device in DEVICE_DATA:
        if device.get("codename", "").lower() == query:
            return device
        if any(query in name.lower() for name in device.get("name", [])):
            return device
    return None

@bot.add_cmd(cmd="whatis")
async def whatis_handler(bot: BOT, message: Message):
    """
    CMD: WHATIS
    INFO: Finds the marketing name of a Xiaomi device by its codename.
    USAGE:
        .whatis [codename]
    EXAMPLE:
        .whatis onyx
    """
    if not message.input:
        await message.reply("Please provide a device codename.", del_in=MEDIUM_TIMEOUT)
        return
        
    progress = await message.reply("<code>Searching...</code>")
    
    device = await find_device(message.input)

    if device:
        firmware_url = f"https://xiaomifirmwareupdater.com/firmware/{device['codename']}/"
        response_text = (
            f"<b>Codename:</b> <code>{safe_escape(device['codename'])}</code>\n"
            f"<b>Device:</b> {safe_escape(' / '.join(device['name']))}\n\n"
            f"<a href='{firmware_url}'>› Download Firmware</a>"
        )
        await progress.edit(response_text, link_preview_options=LinkPreviewOptions(is_disabled=True))
    else:
        await progress.edit(f"<b>Error:</b> Codename <code>{safe_escape(message.input)}</code> not found.", del_in=LONG_TIMEOUT)

@bot.add_cmd(cmd="codename")
async def codename_handler(bot: BOT, message: Message):
    """
    CMD: CODENAME
    INFO: Finds the codename of a Xiaomi device by its marketing name.
    USAGE:
        .codename [marketing name]
    EXAMPLE:
        .codename poco f6
    """
    if not message.input:
        await message.reply("Please provide a marketing name to search for.", del_in=MEDIUM_TIMEOUT)
        return

    progress = await message.reply("<code>Searching...</code>")

    if not DEVICE_DATA:
        await load_device_data()
    if DEVICE_DATA is None:
        await progress.edit("<b>Error:</b> Could not load device database.", del_in=LONG_TIMEOUT)
        return

    search_term = message.input.lower()
    matches = [dev for dev in DEVICE_DATA if any(search_term in name.lower() for name in dev.get("name", []))]
    
    if matches:
        response_text = f"<b>🔍 Found {len(matches)} matching devices:</b>\n\n"
        unique_matches = {f"<code>{safe_escape(' / '.join(dev['name']))}</code> is <b>{safe_escape(dev['codename'])}</b>" for dev in matches}
        response_text += "\n".join(sorted(list(unique_matches)))
        
        if len(response_text) > 4096:
            response_text = response_text[:4000] + "\n\n<b>...and more results. Refine your search.</b>"
        await progress.edit(response_text, link_preview_options=LinkPreviewOptions(is_disabled=True))
    else:
        await progress.edit(f"<b>Error:</b> No devices found matching '<code>{safe_escape(search_term)}</code>'.", del_in=LONG_TIMEOUT)

@bot.add_cmd(cmd="specs")
async def specs_handler(bot: BOT, message: Message):
    """
    CMD: SPECS
    INFO: Shows detailed specifications of a Xiaomi device.
    USAGE:
        .specs [codename | marketing name]
    EXAMPLE:
        .specs garnet
    """
    if not message.input:
        await message.reply("Please provide a device codename or name.", del_in=MEDIUM_TIMEOUT)
        return
    
    progress = await message.reply("<code>Searching for device...</code>")
    
    device = await find_device(message.input)
    if not device:
        await progress.edit(f"<b>Error:</b> Device '<code>{safe_escape(message.input)}</code>' not found.", del_in=LONG_TIMEOUT)
        return
        
    await progress.edit("<code>Found device, fetching specifications...</code>")

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(f"{SPECS_API_URL}{device['codename']}") as response:
                response.raise_for_status()
                specs_data = await response.json()
        
        if not specs_data or not specs_data.get("success"):
            raise ValueError("API returned no data or an error.")
        
        specs = specs_data["data"]
        
        response_text = [f"<b>📱 Specs for {safe_escape(specs['name'])}</b> (<code>{specs['codename']}</code>)\n"]
        for spec_group in specs.get("specifications", []):
            response_text.append(f"\n<b>{html.escape(spec_group['name'])}</b>")
            for detail in spec_group.get("details", []):
                response_text.append(f"  - <b>{html.escape(detail['name'])}:</b> <code>{html.escape(detail['value'])}</code>")
        
        final_message = "\n".join(response_text)
        if len(final_message) > 4096:
            final_message = final_message[:4000] + "\n\n<b>...and more specifications.</b>"

        await progress.edit(final_message)
    except Exception as e:
        await progress.edit(f"<b>Error:</b> Could not fetch specifications. <code>{e}</code>", del_in=LONG_TIMEOUT)
