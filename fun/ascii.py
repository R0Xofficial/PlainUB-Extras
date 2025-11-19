import html
import pyfiglet
from pyrogram.enums import ParseMode

from app import BOT, Message, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

@bot.add_cmd(cmd="ascii")
async def ascii(bot: BOT, message: Message):
    text = message.input
    if not text:
        await message.reply("What am I supposed to say?", del_in=MEDIUM_TIMEOUT)
        return

    ascii_text = pyfiglet.figlet_format(text)

    escaped_ascii_text = html.escape(ascii_text)
    
    await message.reply(f"<b>ASCII:</b>\n<pre>{escaped_ascii_text}</pre>", parse_mode=ParseMode.HTML)
