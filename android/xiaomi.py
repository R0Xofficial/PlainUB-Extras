import httpx
import html
import yaml
from pyrogram.types import Message, LinkPreviewOptions, InlineKeyboardMarkup, InlineKeyboardButton

from app import BOT, bot
from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

MIUI_YAML_URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/latest.yml"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
client = httpx.AsyncClient(headers=HEADERS, http2=True, follow_redirects=True)

@bot.add_cmd(cmd="miui")
async def miui_handler(bot: BOT, message: Message):
    """
    CMD: MIUI
    INFO: Fetches the latest MIUI/HyperOS firmware for a given Xiaomi device codename.
    USAGE:
        .miui [codename]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.miui [codename]</code>", del_in=MEDIUM_TIMEOUT)
        return

    codename = message.input.lower()
    progress = await message.reply(f"<code>Searching for {codename} firmware...</code>")
    
    try:
        response = await client.get(MIUI_YAML_URL, timeout=15)
        response.raise_for_status()
        
        all_firmware = yaml.safe_load(response.text)
        
        matches = [fw for fw in all_firmware if codename in fw.get("codename", "")]
        
        if not matches:
            await progress.edit(f"<b>Error:</b> No MIUI/HyperOS firmware found for codename <code>{codename}</code>.", del_in=LONG_TIMEOUT)
            return
            
        markup = []
        for fw in matches:
            btn_text = (
                f"{fw['version']} ({fw['branch']}) | {fw['android']} | {fw['size']}"
            )
            markup.append([InlineKeyboardButton(text=btn_text, url=fw['link'])])

        device_name = matches[0].get('name', codename.capitalize())
        device_name = device_name.replace(f"({codename})", "").strip()

        msg = f"<b>Latest firmware for {html.escape(device_name)}:</b>"
        
        await progress.edit(
            msg,
            reply_markup=InlineKeyboardMarkup(markup),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
