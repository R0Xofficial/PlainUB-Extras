import os
import html
import asyncio
from gtts import gTTS
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_VISIBLE_DURATION = 8

def safe_escape(text: str) -> str:
    escaped_text = html.escape(str(text))
    return escaped_text.replace("&#x27;", "’")

def sync_gtts(text: str, lang: str) -> str:
    """
    Synchronous function to generate a speech file using gTTS.
    """
    output_path = os.path.join(TEMP_DIR, f"{hash(text + lang)}.mp3")
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_path)
    return output_path

@bot.add_cmd(cmd="tts")
async def tts_handler(bot: BOT, message: Message):
    """
    CMD: TTS
    INFO: Converts text to speech.
    """
    
    text_to_speak, lang = "", "en"

    if message.replied and message.replied.text:
        text_to_speak = message.replied.text
        if message.input: lang = message.input.lower()
    elif message.input:
        parts = message.input.split(maxsplit=1)
        if len(parts) > 1 and len(parts[0]) == 2 and parts[0].isalpha():
            lang, text_to_speak = parts[0].lower(), parts[1]
        else:
            text_to_speak = message.input
    else:
        await message.reply("Please provide text or reply to a message.", del_in=ERROR_VISIBLE_DURATION)
        return

    if not text_to_speak.strip():
        await message.reply("The message contains no text to convert.", del_in=ERROR_VISIBLE_DURATION)
        return

    progress_message = await message.reply("<code>Converting text to speech...</code>")
    
    file_path = ""
    try:
        file_path = await asyncio.to_thread(sync_gtts, text_to_speak, lang)

        await progress_message.edit("<code>Sending...</code>")
        await bot.send_voice(
            chat_id=message.chat.id,
            voice=file_path,
            reply_parameters=ReplyParameters(message_id=message.reply_to_message_id or message.id)
        )
        await progress_message.delete()
        await message.delete()

    except Exception as e:
        await progress_message.edit(f"<b>Error:</b> Could not generate speech.\n<code>{safe_escape(str(e))}</code>")
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try: await message.delete()
        except: pass
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
