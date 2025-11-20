import httpx
import html
from bs4 import BeautifulSoup
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import MEDIUM_TIMEOUT, LARGE_TIMEOUT

# Używamy pełnego zestawu nagłówków, aby idealnie imitować przeglądarkę
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/"
}

# Stworzymy jedną, trwałą sesję klienta, co jest bardziej wydajne
client = httpx.AsyncClient(headers=HEADERS, http2=True, follow_redirects=True)

@bot.add_cmd(cmd="testcheckfw")
async def checkfw_handler(bot: BOT, message: Message):
    """
    CMD: CHECKFW
    INFO: Shows the latest official firmware for a Samsung device from OTA servers.
    USAGE: .checkfw [model] [csc]
    """
    args = message.input.split()
    if len(args) != 2: await message.reply("<b>Usage:</b> <code>.checkfw [model] [csc]</code>", del_in=MEDIUM_TIMEOUT); return
        
    model, csc = args[0].upper(), args[1].upper()
    if not model.startswith("SM-"): model = f"SM-{model}"
        
    progress = await message.reply(f"<code>Checking official Samsung servers for {model}/{csc}...</code>")
    
    try:
        url = f'https://fota-cloud-dn.ospserver.net/firmware/{csc}/{model}/version.xml'
        response = await client.get(url, timeout=10)
        
        if response.status_code != 200:
            await progress.edit(f"<b>Error:</b> No firmware found for <code>{model}/{csc}</code>.", del_in=LARGE_TIMEOUT); return
        
        content = response.text
        soup = BeautifulSoup(content, 'xml')
        latest = soup.find("latest")
        if not latest or not latest.text.strip():
             await progress.edit(f"<b>Error:</b> No public release found for <code>{model}/{csc}</code>.", del_in=LARGE_TIMEOUT); return
        
        pda, csc_ver, phone = (latest.text.strip().split('/') + [None, None])[:3]
        os_ver = latest.get("o", "N/A")

        res_text = [f"<b>📱 Latest Firmware for {model} ({csc})</b>\n", f"<b>PDA:</b> <code>{pda}</code>", f"<b>CSC:</b> <code>{csc_ver}</code>"]
        if phone: res_text.append(f"<b>Phone:</b> <code>{phone}</code>")
        res_text.append(f"<b>Android:</b> <code>{os_ver}</code>")
        await progress.edit("\n".join(res_text))
    except httpx.ConnectTimeout:
        await progress.edit(f"<b>Error:</b> Connection timed out. The server might be down or your network is blocking it.", del_in=LARGE_TIMEOUT)
    except Exception as e:
        await progress.edit(f"<b>An error occurred:</b> <code>{html.escape(str(e))}</code>", del_in=LARGE_TIMEOUT)

# --- Pozostałe komendy (sm, specs) wymagają jeszcze bardziej zaawansowanych metod.
# --- Skupmy się na razie na tym, aby checkfw zadziałało. Jeśli zadziała, to znaczy,
# --- że jesteśmy na dobrej drodze i dodamy resztę w ten sam, niezawodny sposób.

@bot.add_cmd(cmd=["tsm", "tspecs"])
async def placeholder_handler(bot: BOT, message: Message):
    await message.reply("This command is temporarily disabled for a rewrite. Please wait for the fix.", del_in=MEDIUM_TIMEOUT)
