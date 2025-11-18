import os
import html
import asyncio
import qrcode
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_qrcode/"
os.makedirs(TEMP_DIR, exist_ok=True)


@bot.add_cmd(cmd=["mkqr", "makeqr"])
async def make_qr_handler(bot: BOT, message: Message):
    """
    CMD: MAKEQR / MKQR
    INFO: Generates a QR code from the given text, link, or replied-to message.
    USAGE:
        .mkqr [text/link]
        .mkqr (in reply to a message)
    """
    
    data_to_encode = ""
    if message.input:
        data_to_encode = message.input
    elif message.replied and message.replied.text:
        data_to_encode = message.replied.text
    
    if not data_to_encode:
        await message.reply(
            "<b>Usage:</b> <code>.mkqr [text/link]</code> or reply to a message.",
            del_in=8
        )
        return

    progress_msg = await message.reply("<code>Generating QR code...</code>")
    
    output_path = os.path.join(TEMP_DIR, f"qrcode_{message.id}.png")
    
    try:
        def generate_qr_sync():
            qr_img = qrcode.make(data_to_encode)
            qr_img.save(output_path)

        await asyncio.to_thread(generate_qr_sync)

        text_caption = f"Your generated QR code"

        if message.replied:
            await bot.send_photo(
                  chat_id=message.chat.id,
                  photo=output_path,
                  caption=text_caption,
                  reply_parameters = ReplyParameters(message_id=message.replied.id)
            )
        else:
            await bot.send_photo(
                  chat_id=message.chat.id,
                  photo=output_path,
                  caption=text_caption,
                  reply_parameters = ReplyParameters(message_id=message.id)
            )
        
        await progress_msg.delete()

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=10)
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
