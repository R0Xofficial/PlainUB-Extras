import io
import contextlib
import html
from cowsay import cow
from pyrogram.enums import ParseMode

from app import BOT, Message, bot


@bot.add_cmd(cmd="cowsay")
async def cowsay(bot: BOT, message: Message):
    """
    CMD: COWSAY
    INFO: Makes a cow say something.
    USAGE:
        .cowsay [text]
    """
    text = message.input
    if not text:
        await message.reply("What is the cow supposed to say?", del_in=10)
        return

    string_io = io.StringIO()
    with contextlib.redirect_stdout(string_io):
        cow(text)
    
    cow_said = string_io.getvalue()

    if cow_said.endswith('\n'):
        cow_said = cow_said[:-1]

    escaped_cow_text = html.escape(cow_said)
    
    await message.reply(f"<b>Cowsay:</b>\n<pre>{escaped_cow_text}</pre>", parse_mode=ParseMode.HTML)
