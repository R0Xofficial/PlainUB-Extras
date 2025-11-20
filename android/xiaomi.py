import httpx
import html
import yaml
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import MEDIUM_TIMEOUT, LONG_TIMEOUT

DEVICES_YAML_URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/devices.yml"
FIRMWARE_YAML_URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/latest.yml"

DEVICE_DATA = {}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
client = httpx.AsyncClient(headers=HEADERS, http2=True, follow_redirects=True)

async def load_device_data():
    global DEVICE_DATA
    if DEVICE_DATA: return
    try:
        response = await client.get(DEVICES_YAML_URL)
        response.raise_for_status()
        raw_data = yaml.safe_load(response.text)
        clean_data = {}
        for codename, names in raw_data.items():
            if names and isinstance(names, list):
                clean_data[codename] = names[0]
        DEVICE_DATA = clean_data
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
    progress = await message.reply("<code>Searching device...</code>")
    
    if not DEVICE_DATA: await load_device_data()
    if DEVICE_DATA is None: await progress.edit("<b>Error:</b> Could not load device database.", del_in=LONG_TIMEOUT); return
    
    codename = message.input.lower()
    
    if codename in DEVICE_DATA:
        marketing_name = DEVICE_DATA[codename]
        res = f"<code>{safe_escape(codename)}</code> is <b>{safe_escape(marketing_name)}</b>"
        await progress.edit(res)
    else:
        await progress.edit(f"<code>{safe_escape(codename)}</code> not found.", del_in=LONG_TIMEOUT)

@bot.add_cmd(cmd="codename")
async def codename_handler(bot: BOT, message: Message):
    """
    CMD: CODENAME
    INFO: Finds the codename of a Xiaomi device by its marketing name.
    USAGE:
        .codename [marketing name]
    """
    if not message.input: await message.reply("Please provide a name.", del_in=MEDIUM_TIMEOUT); return
    progress = await message.reply("<code>Searching device...</code>")
    if not DEVICE_DATA: await load_device_data()
    if DEVICE_DATA is None: await progress.edit("<b>Error:</b> Could not load device database.", del_in=LONG_TIMEOUT); return

    term = message.input.lower()
    matches = {codename: name for codename, name in DEVICE_DATA.items() if term in name.lower()}
    
    if matches:
        header = f"<b>🔍 Found {len(matches)} matching devices:</b>"
        formatted_lines = [f"<code>{safe_escape(name)}</code> is <b>{safe_escape(codename)}</b>" for codename, name in matches.items()]
        blockquote_content = "\n".join(sorted(formatted_lines))
        res = f"{header}\n<blockquote>{blockquote_content}</blockquote>"
        
        if len(res) > 4096:
            res = f"<b>🔍 Found {len(matches)} matching devices (showing truncated list):</b>\n\n"
            res += "\n".join(sorted(formatted_lines))
            res = res[:4000] + "\n\n<b>...and more results. Refine your search.</b>"
            
        await progress.edit(res, link_preview_options=LinkPreviewOptions(is_disabled=True))
    else:
        await progress.edit(f"No devices found matching '<code>{safe_escape(term)}</code>'.", del_in=LONG_TIMEOUT)

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
    progress = await message.reply(f"<code>Searching firmware...</code>")
    
    try:
        target_codename = query
        
        if not DEVICE_DATA: await load_device_data()
        if DEVICE_DATA is not None and query not in DEVICE_DATA:
            possible_devices = {codename: name for codename, name in DEVICE_DATA.items() if query in name.lower()}
            
            if len(possible_devices) == 1:
                target_codename = list(possible_devices.keys())[0]
            elif len(possible_devices) > 1:
                header = f"<b>Query is ambiguous. Found {len(possible_devices)} devices:</b>"
                formatted_lines = [f"<code>{safe_escape(name)}</code> is <b>{safe_escape(codename)}</b>" for codename, name in possible_devices.items()]
                blockquote_content = "\n".join(sorted(formatted_lines))
                
                res = (
                    f"{header}\n<blockquote expandable>{blockquote_content}</blockquote>\n"
                    "Please try again with a more specific name or use the exact codename."
                )
                
                await progress.edit(res, link_preview_options=LinkPreviewOptions(is_disabled=True))
                return
        
        if DEVICE_DATA is not None:
            target_device_name = DEVICE_DATA.get(target_codename, query.capitalize())
        else:
            target_device_name = query.capitalize()
        
        response = await client.get(FIRMWARE_YAML_URL, timeout=15)
        response.raise_for_status()
        all_firmware = yaml.safe_load(response.text)
        
        matches = []
        for fw in all_firmware:
            codename_field = fw.get("codename")
            if not codename_field: continue
            if isinstance(codename_field, list):
                if target_codename in [c.lower() for c in codename_field]: matches.append(fw)
            elif isinstance(codename_field, str):
                if target_codename == codename_field.lower(): matches.append(fw)
        
        if not matches:
            await progress.edit(f"No firmware found for <code>{query}</code>.", del_in=LONG_TIMEOUT); return
            
        response_text = [f"<b>Latest firmware for {html.escape(target_device_name)} (<code>{target_codename}</code>):</b>"]
        
        for fw in matches[:5]:
            line = (f"\n› <a href=\"{fw['link']}\"><b>{fw['version']}</b> ({fw['branch']})</a>\n"
                    f"  └ <b>Android:</b> <code>{fw['android']}</code> | <b>Size:</b> <code>{fw['size']}</code>")
            response_text.append(line)
        
        await progress.edit("\n".join(response_text), link_preview_options=LinkPreviewOptions(is_disabled=True))
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
