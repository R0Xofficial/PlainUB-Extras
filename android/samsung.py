import aiohttp
import html
from bs4 import BeautifulSoup
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

SAMSUNG_API_URL = "https://api.rev-tech.me/v1/samsung/details/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"}

@bot.add_cmd(cmd="checkfw")
async def checkfw_handler(bot: BOT, message: Message):
    """
    CMD: CHECKFW
    INFO: Shows the latest official firmware for a Samsung device from OTA servers.
    USAGE:
        .checkfw [model] [csc]
    """
    args = message.input.split()
    if len(args) != 2:
        await message.reply("<b>Usage:</b> <code>.checkfw [model] [csc]</code>", del_in=MEDIUM_TIMEOUT)
        return
        
    model, csc = args[0].upper(), args[1].upper()
    if not model.startswith("SM-"):
        model = f"SM-{model}"
        
    progress = await message.reply(f"<code>Checking official Samsung servers for {model}/{csc}...</code>")
    
    try:
        url = f'https://fota-cloud-dn.ospserver.net/firmware/{csc}/{model}/version.xml'
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await progress.edit(f"<b>Error:</b> No firmware found for <code>{model}/{csc}</code>.", del_in=LONG_TIMEOUT)
                    return
                
                content = await response.text()
                soup = BeautifulSoup(content, 'xml')
                
                latest_tag = soup.find("latest")
                if not latest_tag or not latest_tag.text.strip():
                     await progress.edit(f"<b>Error:</b> No public release found for <code>{model}/{csc}</code>.", del_in=LONG_TIMEOUT)
                     return
                
                pda, csc_ver, phone = (latest_tag.text.strip().split('/') + [None, None])[:3]
                os_ver = latest_tag.get("o", "N/A")

                response_text = [
                    f"<b>📱 Latest Firmware for {model} ({csc})</b>\n",
                    f"<b>PDA:</b> <code>{pda}</code>",
                    f"<b>CSC:</b> <code>{csc_ver}</code>",
                ]
                if phone:
                    response_text.append(f"<b>Phone:</b> <code>{phone}</code>")
                response_text.append(f"<b>Android:</b> <code>{os_ver}</code>")

                await progress.edit("\n".join(response_text))
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)

async def get_samsung_specs(query: str):
    """Internal function to fetch device data from the API."""
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(f"{SAMSUNG_API_URL}{query.upper()}") as response:
            if response.status != 200: return None
            data = await response.json()
            return data if data.get("success") else None

@bot.add_cmd(cmd="sm")
async def sm_lookup_handler(bot: BOT, message: Message):
    """
    CMD: SM
    INFO: Finds the marketing name of a Samsung device by its model code.
    USAGE:
        .sm [model_code]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.sm [model_code]</code>", del_in=MEDIUM_TIMEOUT)
        return
        
    model = message.input
    progress = await message.reply(f"<code>Looking up {model.upper()}...</code>")
    
    try:
        data = await get_samsung_specs(model)
        if data:
            await progress.edit(f"Code <code>{model.upper()}</code> belongs to <b>{html.escape(data['data']['name'])}</b>.")
        else:
            await progress.edit(f"<b>Error:</b> Could not find a device for code <code>{model.upper()}</code>.", del_in=LONG_TIMEOUT)
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)

@bot.add_cmd(cmd="specs")
async def specs_handler_samsung(bot: BOT, message: Message):
    """
    CMD: SPECS (Samsung)
    INFO: Shows detailed specifications of a Samsung device.
    USAGE:
        .specs [model_code]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.specs [model_code]</code>", del_in=MEDIUM_TIMEOUT)
        return
        
    query = message.input
    progress = await message.reply(f"<code>Searching for '{query}'...</code>")
    
    try:
        data = await get_samsung_specs(query)
        if not data:
            await progress.edit(f"<b>Error:</b> Could not find specs for '<code>{html.escape(query)}</code>'.", del_in=LONG_TIMEOUT)
            return
            
        specs = data["data"]
        response_text = [f"<b>📱 Specs for {html.escape(specs['name'])}</b>\n"]
        for spec_group in specs.get("specifications", []):
            response_text.append(f"\n<b>{html.escape(spec_group['name'])}</b>")
            for detail in spec_group.get("details", []):
                response_text.append(f"  - <b>{html.escape(detail['name'])}:</b> <code>{html.escape(detail['value'])}</code>")
        
        final_message = "\n".join(response_text)
        if len(final_message) > 4096:
            final_message = final_message[:4000] + "\n\n<b>...and more specifications.</b>"

        await progress.edit(final_message)
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
