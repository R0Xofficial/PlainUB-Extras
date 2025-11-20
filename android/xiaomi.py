import asyncio
import html
import aiohttp
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

DEVICES_JSON_URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/mi-firmware-updater/master/data/devices.json"
SPECS_API_URL = "https://xiaomifirmwareupdater.com/api/v1/specs/"

DEVICE_DATA = []

async def load_device_data():
    global DEVICE_DATA
    if DEVICE_DATA:
        return
    try:
        async with aiohttp.ClientSession() as session:
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
    USAGE: .whatis [codename]
    """
    if not message.input:
        await message.reply("Please provide a device codename.", del_in=MEDIUM_TIMEOUT); return
        
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
    USAGE: .codename [marketing name]
    """
    if not message.input:
        await message.reply("Please provide a marketing name to search for.", del_in=MEDIUM_TIMEOUT); return

    progress = await message.reply("<code>Searching...</code>")

    if not DEVICE_DATA:
        await load_device_data()
        if DEVICE_DATA is None:
            await progress.edit("<b>Error:</b> Could not load device database.", del_in=LONG_TIMEOUT); return

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

@bot.add_cmd(cmd="xspecs")
async def specs_handler(bot: BOT, message: Message):
    """
    CMD: XSPECS
    INFO: Shows the specifications of a Xiaomi device.
    USAGE: .xspecs [codename | marketing name]
    """
    if not message.input:
        await message.reply("Please provide a device codename or name.", del_in=MEDIUM_TIMEOUT); return
    
    progress = await message.reply("<code>Searching for device...</code>")
    
    device = await find_device(message.input)
    if not device:
        await progress.edit(f"<b>Error:</b> Device '<code>{safe_escape(message.input)}</code>' not found.", del_in=LONG_TIMEOUT); return
        
    await progress.edit("<code>Found device, fetching specifications...</code>")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SPECS_API_URL}{device['codename']}") as response:
                response.raise_for_status()
                specs = await response.json()
        
        if not specs:
            raise ValueError("No specifications found for this device.")

        response_text = [
            f"<b>📱 Specs for {safe_escape(' / '.join(specs['name']))}</b> (<code>{specs['codename']}</code>)\n",
            f"<b>Chipset:</b> <code>{safe_escape(specs.get('cpu', 'N/A'))}</code>",
            f"<b>RAM:</b> <code>{safe_escape(specs.get('ram', 'N/A'))}</code>",
            f"<b>Display:</b> <code>{safe_escape(specs.get('display', 'N/A'))}</code>",
            f"<b>Camera:</b> <code>{safe_escape(specs.get('camera', 'N/A'))}</code>",
            f"<b>Battery:</b> <code>{safe_escape(specs.get('battery', 'N/A'))}</code>"
        ]
        await progress.edit("\n".join(response_text))
    except Exception as e:
        await progress.edit(f"<b>Error:</b> Could not fetch specifications. <code>{e}</code>", del_in=LONG_TIMEOUT)
