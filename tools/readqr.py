import os
import html
import asyncio
from PIL import Image
from pyzbar.pyzbar import decode
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_readqr/"
os.makedirs(TEMP_DIR, exist_ok=True)


@bot.add_cmd(cmd=["readqr", "rqr"])
async def read_qr_handler(bot: BOT, message: Message):
    """
    CMD: READQR / RQR
    INFO: Reads a QR code from a replied-to image or sticker.
    USAGE:
        .readqr (in reply to an image or sticker with a QR code)
    """
    
    replied_msg = message.replied
    
    has_media = replied_msg and (replied_msg.photo or replied_msg.sticker)
    
    if not has_media:
        await message.reply("Please reply to an image or sticker containing a QR code.", del_in=8)
        return

    progress_msg = await message.reply("<code>Reading QR code...</code>")
    
    downloaded_path = None
    try:
        downloaded_path = await bot.download_media(replied_msg, file_name=TEMP_DIR)
        
        def decode_qr_sync():
            img = Image.open(downloaded_path)
            
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            return decode(img)

        decoded_objects = await asyncio.to_thread(decode_qr_sync)
        
        if not decoded_objects:
            await progress_msg.edit("<b>No QR code found in the media.</b>", del_in=10)
            return

        qr_data = decoded_objects[0].data.decode("utf-8")
        
        output_text = (f"<b>QR Code Content:</b>\n"
                       f"<pre><code>{html.escape(qr_data)}</code></pre>")

        await bot.send_message(
            chat_id=message.chat.id,
            text=output_text,
            reply_parameters = ReplyParameters(message_id=replied_msg.id)
        )
        
        await progress_msg.delete()
        await message.delete()

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=10)
    finally:
        if downloaded_path and os.path.exists(downloaded_path):
            os.remove(downloaded_path)
