import httpx
import html
import yaml
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import MEDIUM_TIMEOUT, LARGE_TIMEOUT

DEVICES_YAML_URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/devices.yml"
FIRMWARE_YAML_URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/latest.yml"

DEVICE_DATA = []
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
client = httpx.AsyncClient(headers=HEADERS, http2=True, follow_redirects=True)

async def load_device_data():
    global DEVICE_DATA
    if DEVICE_DATA: return
    try:
        response = await client.get(DEVICES_YAML_URL)
        response.raise_for_status()
        DEVICE_DATA = yaml.safe_load(response.text)
    except Exception:
        DEVICE_DATA = None

def safe_escape(text: str) -> str:
    return html.escape(str(text))

@bot.add_cmd(cmd="whatis")
async def whatis_handler(bot: BOT, message: Message):
    """
    CMD: WHATIS
    INFO: Finds the marketing name of a Xiaomi device by its codename.
    USAGE:
        .whatis [codename]
    """
    if not message.input: await message.reply("Please provide a codename.", del_in=MEDIUM_TIMEOUT); return
    progress = await message.reply("<code>Searching...</code>")
    
    if not DEVICE_DATA: await load_device_data()
    if DEVICE_DATA is None: await progress.edit("<b>Error:</b> Could not load device database.", del_in=LARGE_TIMEOUT); return
    
    codename = message.input.lower()
    device = next((d for d in DEVICE_DATA if d.get("codename", "").lower() == codename), None)
    
    if device:
        res = f"<b>Codename:</b> <code>{safe_escape(device['codename'])}</code> is <b>{safe_escape(' / '.join(device['name']))}</b>"
        await progress.edit(res)
    else:
        await progress.edit(f"<b>Error:</b> Codename <code>{safe_escape(codename)}</code> not found.", del_in=LARGE_TIMEOUT)

@bot.add_cmd(cmd="codename")
async def codename_handler(bot: BOT, message: Message):
    """
    CMD: CODENAME
    INFO: Finds the codename of a Xiaomi device by its marketing name.
    USAGE:
        .codename [marketing name]
    """
    if not message.input: await message.reply("Please provide a name.", del_in=MEDIUM_TIMEOUT); return
    progress = await message.reply("<code>Searching...</code>")
    if not DEVICE_DATA: await load_device_data()
    if DEVICE_DATA is None: await progress.edit("<b>Error:</b> Could not load device database.", del_in=LARGE_TIMEOUT); return

    term = message.input.lower()
    matches = [d for d in DEVICE_DATA if any(term in n.lower() for n in d.get("name", []))]
    if matches:
        res = f"<b>Found {len(matches)} matching devices:</b>\n\n"
        unique = {f"<code>{safe_escape(' / '.join(d['name']))}</code> is <b>{safe_escape(d['codename'])}</b>" for d in matches}
        res += "\n".join(sorted(list(unique)))
        if len(res) > 4096: res = res[:4000] + "\n\n<b>...and more results. Refine your search.</b>"
        await progress.edit(res, link_preview_options=LinkPreviewOptions(is_disabled=True))
    else:
        await progress.edit(f"<b>Error:</b> No devices found matching '<code>{safe_escape(term)}</code>'.", del_in=LARGE_TIMEOUT)

@bot.add_cmd(cmd="miui")
async def miui_handler(bot: BOT, message: Message):
    """
    CMD: MIUI
    INFO: Fetches the latest MIUI/HyperOS firmware for a given Xiaomi device.
    USAGE:
        .miui [codename | marketing name]
    """
    if not message.input: await message.reply("<b>Usage:</b> <code>.miui [codename | name]</code>", del_in=MEDIUM_TIMEOUT); return

    query = message.input.lower()
    progress = await message.reply(f"<code>Searching for {query} firmware...</code>")
    
    try:
        response = await client.get(FIRMWARE_YAML_URL, timeout=15)
        response.raise_for_status()
        all_firmware = yaml.safe_load(response.text)
        
        matches = []
        for fw in all_firmware:
            codename_field = fw.get("codename")
            if not codename_field: continue
            if isinstance(codename_field, list) and query in [c.lower() for c in codename_field]:
                matches.append(fw)
            elif isinstance(codename_field, str) and query == codename_field.lower():
                matches.append(fw)

        if not matches:
            if not DEVICE_DATA: await load_device_data()
            if DEVICE_DATA is None: await progress.edit("<b>Error:</b> Could not load device database.", del_in=LARGE_TIMEOUT); return
            
            possible_devices = [d for d in DEVICE_DATA if any(query in n.lower() for n in d.get("name", []))]
            if len(possible_devices) == 1:
                codename_from_name = possible_devices[0].get("codename", "").lower()
                for fw in all_firmware:
                    codename_field = fw.get("codename")
                    if not codename_field: continue
                    if isinstance(codename_field, list) and codename_from_name in [c.lower() for c in codename_field]:
                        matches.append(fw)
                    elif isinstance(codename_field, str) and codename_from_name == codename_field.lower():
                        matches.append(fw)

            elif len(possible_devices) > 1:
                res = f"<b>Query is ambiguous. Found {len(possible_devices)} devices:</b>\n\n"
                unique = {f"<code>{safe_escape(' / '.join(d['name']))}</code> is <b>{safe_escape(d['codename'])}</b>" for d in possible_devices}
                res += "\n".join(sorted(list(unique)))
                res += "\n\nPlease try again with a more specific name or use the exact codename."
                await progress.edit(res, link_preview_options=LinkPreviewOptions(is_disabled=True)); return
        
        if not matches:
            await progress.edit(f"<b>Error:</b> No firmware found for <code>{query}</code>.", del_in=LARGE_TIMEOUT); return
            
        device_name = matches[0].get('name', query.capitalize()).split('(')[0].strip()
        response_text = [f"<b>Latest firmware for {html.escape(device_name)}:</b>"]
        
        for fw in matches[:5]:
            line = (
                f"\n› <a href=\"{fw['link']}\"><b>{fw['version']}</b> ({fw['branch']})</a>\n"
                f"  └ <b>Android:</b> <code>{fw['android']}</code> | <b>Size:</b> <code>{fw['size']}</code>"
            )
            response_text.append(line)
        
        await progress.edit("\n".join(response_text), link_preview_options=LinkPreviewOptions(is_disabled=True))

    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LARGE_TIMEOUT)
