import html
import asyncio
from deep_translator import GoogleTranslator
from pyrogram.types import LinkPreviewOptions, Message

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

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
        .tr -[lang] [text] (e.g., .tr -pl Hello)
        .tr -[lang] (reply to a message)
    NOTE: Default target language is English (en).
    """
    
    target_lang = DEFAULT_TARGET_LANG
    text_to_translate = ""

    if message.replied and (message.replied.text or message.replied.caption):
        text_to_translate = message.replied.text or message.replied.caption
        if message.input and message.input.startswith('-'):
            target_lang = message.input[1:].lower()
    
    elif message.input:
        parts = message.input.split(maxsplit=1)
        if len(parts) > 1 and parts[0].startswith('-'):
            target_lang = parts[0][1:].lower()
            text_to_translate = parts[1]
        else:
            text_to_translate = message.input
    else:
        await message.reply("Please provide text to translate or reply to a message.", del_in=MEDIUM_TIMEOUT)
        return

    if not text_to_translate.strip():
        await message.reply("The message contains no text to translate.", del_in=MEDIUM_TIMEOUT)
        return

    progress_message = await message.reply("<code>Translating...</code>")
    
    try:
        translated_text, detected_source = await asyncio.to_thread(
            sync_translate,
            text=text_to_translate,
            target=target_lang
        )
        
        final_text = (
            f"<b>🌍 Translation to: {target_lang}</b>\n\n"
            f"<b>Input:</b>\n<blockquote expandable>{safe_escape(text_to_translate)}</blockquote>\n\n"
            f"<b>Output:</b>\n<blockquote expandable>{safe_escape(translated_text)}</blockquote>"
        )
        
        await progress_message.edit(
            final_text,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    except Exception as e:
        if "invalid destination language" in str(e).lower():
            error_text = f"<b>Invalid language code:</b> <code>{safe_escape(target_lang)}</code>"
        else:
            error_text = f"<b>An error occurred:</b>\n<code>{safe_escape(str(e))}</code>"
            
        await progress_message.edit(error_text, del_in=LARGE_TIMEOUT)
