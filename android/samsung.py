import httpx
import html
import xml.etree.ElementTree as ET
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"}
client = httpx.AsyncClient(headers=HEADERS, http2=True, follow_redirects=True)

async def get_samsung_ota_data(model: str, csc: str):
    url = f'https://fota-cloud-dn.ospserver.net/firmware/{csc}/{model}/version.xml'
    response = await client.get(url, timeout=10)
    if response.status_code != 200:
        return None
    
    root = ET.fromstring(response.content)
    latest = root.find("./firmware/version/latest")
    
    if latest is None or not latest.text or not latest.text.strip():
        return None
        
    pda, csc_ver, phone = (latest.text.strip().split('/') + [None, None])[:3]
    os_ver = latest.attrib.get("o", "N/A")
    return {"pda": pda, "csc_ver": csc_ver, "phone": phone, "os": os_ver}

@bot.add_cmd(cmd="checkfw")
async def checkfw_handler(bot: BOT, message: Message):
    """
    CMD: CHECKFW
    INFO: Shows the latest official firmware for a Samsung device.
    USAGE: .checkfw [model] [csc]
    """
    args = message.input.split()
    if len(args) != 2: await message.reply("<b>Usage:</b> <code>.checkfw [model] [csc]</code>", del_in=MEDIUM_TIMEOUT); return
        
    model, csc = args[0].upper(), args[1].upper()
    if not model.startswith("SM-"): model = f"SM-{model}"
        
    progress = await message.reply(f"<code>Checking official Samsung servers for {model}/{csc}...</code>")
    
    try:
        data = await get_samsung_ota_data(model, csc)
        if not data:
            await progress.edit(f"<b>Error:</b> No firmware found for <code>{model}/{csc}</code>.", del_in=LONG_TIMEOUT); return
        
        res = [f"<b>Latest Firmware for {model} ({csc})</b>\n", f"<b>PDA:</b> <code>{data['pda']}</code>", f"<b>CSC:</b> <code>{data['csc_ver']}</code>"]
        if data['phone']: res.append(f"<b>Phone:</b> <code>{data['phone']}</code>")
        res.append(f"<b>Android:</b> <code>{data['os']}</code>")
        await progress.edit("\n".join(res))
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)

@bot.add_cmd(cmd="getfw")
async def getfw_handler(bot: BOT, message: Message):
    """
    CMD: GETFW
    INFO: Provides download links for a Samsung device's firmware.
    USAGE: .getfw [model] [csc]
    """
    args = message.input.split()
    if len(args) != 2: await message.reply("<b>Usage:</b> <code>.getfw [model] [csc]</code>", del_in=MEDIUM_TIMEOUT); return
        
    model, csc = args[0].upper(), args[1].upper()
    if not model.startswith("SM-"): model = f"SM-{model}"

    progress = await message.reply(f"<code>Fetching info and links for {model}/{csc}...</code>")
    
    try:
        data = await get_samsung_ota_data(model, csc)
        if not data:
            await progress.edit(f"<b>Error:</b> No firmware found for <code>{model}/{csc}</code> to generate links.", del_in=LONG_TIMEOUT); return
            
        res = [f"<b>Latest Firmware for {model} ({csc})</b>\n", f"<b>PDA:</b> <code>{data['pda']}</code>", f"<b>CSC:</b> <code>{data['csc_ver']}</code>"]
        if data['phone']: res.append(f"<b>Phone:</b> <code>{data['phone']}</code>")
        res.append(f"<b>Android:</b> <code>{data['os']}</code>\n")
        res.append(f"<b>Download links for {model}:</b>")
        
        res.append(f"  › <a href='https://samfw.com/firmware/{model}/{csc}/'>SamFW (Recommended)</a>")
        res.append(f"  › <a href='https://samfrew.com/model/{model}/region/{csc}/'>Samfrew</a>")
        res.append(f"  › <a href='https://www.sammobile.com/samsung/firmware/{model}/{csc}/'>Sammobile</a>")
        res.append(f"  › <a href='https://sfirmware.com/samsung-{model.lower()}/#tab=firmwares'>SFirmware</a>")
        
        await progress.edit("\n".join(res), link_preview_options=LinkPreviewOptions(is_disabled=True))

    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
