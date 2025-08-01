import html
import pyfiglet
from pyrogram.enums import ParseMode

from app import BOT, Message, bot


@bot.add_cmd(cmd="ascii")
async def ascii(bot: BOT, message: Message):
    text = message.input
    if not text:
        await message.reply("What am I supposed to say?")
        return

    ascii_text = pyfiglet.figlet_format(text)

    escaped_ascii_text = html.escape(ascii_text)
    
    await message.reply(f"<pre class=ASCII>{escaped_ascii_text}</pre>", parse_mode=ParseMode.HTML)
