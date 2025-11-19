import html
from pyrogram.types import Message, ReplyParameters
from pyrogram.enums import ParseMode

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

@bot.add_cmd(cmd="noformat")
async def noformat_handler(bot: BOT, message: Message):
    """
    CMD: NOFORMAT
    INFO: Shows the raw, unformatted text of a replied-to message, including its formatting characters.
    USAGE:
        .noformat (in reply to a message)
    """
    replied_msg = message.replied
    
    if not replied_msg:
        await message.reply("Please reply to a message to see its raw format.", del_in=MEDIUM_TIMEOUT)
        return

    raw_markdown = None
    if replied_msg.text:
        raw_markdown = replied_msg.text.markdown
    elif replied_msg.caption:
        raw_markdown = replied_msg.caption.markdown
        
    if not raw_markdown:
        await message.reply("The replied-to message does not contain any formattable text.", del_in=MEDIUM_TIMEOUT)
        return

    escaped_markdown = html.escape(raw_markdown)
    
    output_text = (f"<b>Raw Markdown Content:</b>\n"
                   f"<pre>{escaped_markdown}</pre>")

    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=output_text,
            reply_parameters = ReplyParameters(message_id=replied_msg.id),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        await message.reply(f"<b>Error:</b> Could not send raw format.\n<code>{html.escape(str(e))}</code>", del_in=LARGE_TIMEOUT)
