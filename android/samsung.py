import aiohttp
import html
from bs4 import BeautifulSoup
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

async def scrape_latest_firmware(model: str, csc: str) -> dict | None:
    url = f"https://samfw.com/firmware/{model.upper()}/{csc.upper()}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200: return None
            
            soup = BeautifulSoup(await response.text(), "html.parser")
            device_name_tag = soup.find("h1")
            device_name = device_name_tag.text.strip().replace("firmware", "").strip() if device_name_tag else model.upper()
            table = soup.find("table", class_="table-bordered")
            if not table: return None
            first_row = table.find("tbody").find("tr")
            if not first_row: return None
            columns = first_row.find_all("td")
            if len(columns) < 5: return None
            
            return {
                "device": device_name, "csc": csc.upper(), "version": columns[0].text.strip(),
                "os": columns[1].text.strip(), "build_date": columns[2].text.strip(),
                "security_patch": columns[3].text.strip(), "bit_rev": columns[4].text.strip(),
            }

async def find_device_specs(query: str) -> dict | None:
    """Scrapes GSMArena for device specs."""
    url = f"https://www.gsmarena.com/res.php3?sSearch={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Find the device page URL
        async with session.get(url, headers=headers) as response:
            if response.status != 200: return None
            soup = BeautifulSoup(await response.text(), "html.parser")
            makers = soup.find('div', class_='makers')
            if not makers: return None
            device_link = makers.find('a')
            if not device_link or not device_link.has_attr('href'): return None
            device_url = "https://www.gsmarena.com/" + device_link['href']

        # Step 2: Scrape the device page
        async with session.get(device_url, headers=headers) as response:
            if response.status != 200: return None
            soup = BeautifulSoup(await response.text(), "html.parser")
            
            name = soup.find('h1', class_='specs-phone-name-title').text.strip()
            specs = {
                "name": name,
                "chipset": soup.find('td', {'data-spec': 'chipset'}).text.strip(),
                "cpu": soup.find('td', {'data-spec': 'cpu'}).text.strip(),
                "display": soup.find('td', {'data-spec': 'displaytype'}).text.strip(),
                "resolution": soup.find('td', {'data-spec': 'displayresolution'}).text.strip(),
                "ram_storage": soup.find('td', {'data-spec': 'internalmemory'}).text.strip(),
                "camera": soup.find('td', {'data-spec': 'cam1modules'}).text.strip(),
                "battery": soup.find('td', {'data-spec': 'batdescription1'}).text.strip(),
            }
            return specs

@bot.add_cmd(cmd="checkfw")
async def checkfw_handler(bot: BOT, message: Message):
    """
    CMD: CHECKFW
    INFO: Fetches the latest firmware for a Samsung device from SamFW.
    USAGE: .checkfw [model] [csc]
    """
    args = message.input.split()
    if len(args) != 2:
        await message.reply("<b>Usage:</b> <code>.checkfw [model] [csc]</code>", del_in=MEDIUM_TIMEOUT)
        return
    model, csc = args[0], args[1]
    progress = await message.reply(f"<code>Checking for {model.upper()}/{csc.upper()}...</code>")
    
    try:
        fw = await scrape_latest_firmware(model, csc)
        if not fw:
            await progress.edit(f"<b>Error:</b> Could not find firmware for <code>{model.upper()}/{csc.upper()}</code>.", del_in=LONG_TIMEOUT)
            return
            
        result = (
            f"<b>📱 Latest Firmware Found</b>\n\n"
            f"<b>Device:</b> <code>{html.escape(fw['device'])}</code>\n"
            f"<b>CSC:</b> <code>{html.escape(fw['csc'])}</code>\n"
            f"<b>Version:</b> <code>{html.escape(fw['version'])}</code>\n"
            f"<b>Bit/SW REV:</b> <code>{html.escape(fw['bit_rev'])}</code>\n"
            f"<b>Security Patch:</b> <code>{html.escape(fw['security_patch'])}</code>\n"
            f"<b>OS:</b> <code>{html.escape(fw['os'])}</code>\n"
            f"<b>Build Date:</b> <code>{html.escape(fw['build_date'])}</code>"
        )
        await progress.edit(result, link_preview_options=LinkPreviewOptions(is_disabled=True))
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b>\n<code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)

@bot.add_cmd(cmd="sm")
async def sm_lookup_handler(bot: BOT, message: Message):
    """
    CMD: SM
    INFO: Finds the marketing name of a Samsung device by its SM- code.
    USAGE: .sm [model_code]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.sm [model_code]</code> (e.g., SM-S928B)", del_in=MEDIUM_TIMEOUT)
        return
    model = message.input
    progress = await message.reply(f"<code>Looking up {model.upper()}...</code>")

    try:
        specs = await find_device_specs(model)
        if specs:
            await progress.edit(f"Code <code>{model.upper()}</code> belongs to <b>{html.escape(specs['name'])}</b>.")
        else:
            await progress.edit(f"<b>Error:</b> Could not find a device for code <code>{model.upper()}</code>.", del_in=LONG_TIMEOUT)
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b>\n<code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)

@bot.add_cmd(cmd="smspecs")
async def specs_handler(bot: BOT, message: Message):
    """
    CMD: SMSPECS
    INFO: Shows the specifications of a Samsung device.
    USAGE: .smspecs [model_code | marketing name]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.specs [model_code | name]</code>", del_in=MEDIUM_TIMEOUT)
        return
    query = message.input
    progress = await message.reply(f"<code>Searching for '{query}'...</code>")

    try:
        specs = await find_device_specs(query)
        if not specs:
            await progress.edit(f"<b>Error:</b> Could not find specifications for '<code>{html.escape(query)}</code>'.", del_in=LONG_TIMEOUT)
            return
        
        result = (
            f"<b>📱 Specs for {html.escape(specs['name'])}</b>\n\n"
            f"<b>Chipset:</b> <code>{html.escape(specs['chipset'])}</code>\n"
            f"<b>CPU:</b> <code>{html.escape(specs['cpu'])}</code>\n"
            f"<b>Display:</b> <code>{html.escape(specs['display'])} ({html.escape(specs['resolution'])})</code>\n"
            f"<b>Memory:</b> <code>{html.escape(specs['ram_storage'])}</code>\n"
            f"<b>Main Camera:</b> <code>{html.escape(specs['camera'])}</code>\n"
            f"<b>Battery:</b> <code>{html.escape(specs['battery'])}</code>"
        )
        await progress.edit(result)
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b>\n<code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
