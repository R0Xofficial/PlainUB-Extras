import html
import asyncio
from deep_translator import GoogleTranslator
from pyrogram.types import LinkPreviewOptions, Message

from app import BOT, bot

ERROR_VISIBLE_DURATION = 8
DEFAULT_TARGET_LANG = "en"

def safe_escape(text: str) -> str:
    escaped_text = html.escape(str(text))
    return escaped_text.replace("&#x27;", "’")

def sync_translate(text: str, target: str) -> tuple[str, str]:
    """
    Synchronous function to perform translation with auto-detection.
    Returns a tuple of (translated_text, detected_source_language).
    """
    translator = GoogleTranslator(source="auto", target=target)
    translated_text = translator.translate(text)
    detected_source = translator.get_supported_languages(as_dict=True).get(translator.source, translator.source)
    return translated_text, detected_source

@bot.add_cmd(cmd=["tr", "translate"])
async def translate_handler(bot: BOT, message: Message):
    """
    CMD: TR | TRANSLATE
    INFO: Translates text to a specified language.
    USAGE:
        .tr [to_lang] [text] (e.g., .tr pl Hello)
        .tr [to_lang] (reply to a message)
    NOTE: Default target language is English (en).
    """
    
    target_lang = DEFAULT_TARGET_LANG
    text_to_translate = ""

    if message.replied and (message.replied.text or message.replied.caption):
        text_to_translate = message.replied.text or message.replied.caption
        if message.input:
            target_lang = message.input.lower()
    
    elif message.input:
        parts = message.input.split(maxsplit=1)
        if len(parts) == 2:
            target_lang = parts[0].lower()
            text_to_translate = parts[1]
        else:
            text_to_translate = message.input
    else:
        await message.edit("Please provide text to translate or reply to a message.")
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await message.delete()
        return

    if not text_to_translate.strip():
        await message.edit("The message contains no text to translate.")
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await message.delete()
        return

    progress_message = await message.reply("Translating...")
    
    try:
        translated_text, detected_source = await asyncio.to_thread(
            sync_translate,
            text=text_to_translate,
            target=target_lang
        )
        
        final_text = (
            f"<b>🌍 Translation | {detected_source} → {target_lang}</b>\n\n"
            f"<b>Input:</b>\n<blockquote expandable>{safe_escape(text_to_translate)}</blockquote>\n"
            f"<b>Output:</b>\n<blockquote expandable>{safe_escape(translated_text)}</blockquote>"
        )
        
        await progress_message.edit(
            final_text,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
        await message.delete()

    except Exception as e:
        if "invalid destination language" in str(e).lower():
            error_text = f"<b>Invalid language code:</b> <code>{safe_escape(target_lang)}</code>"
        else:
            error_text = f"<b>An error occurred:</b>\n<code>{safe_escape(str(e))}</code>"
            
        await progress_message.edit(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
        try:
            await message.delete()
        except Exception:
            pass
