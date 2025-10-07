import asyncio
import html
import re
from datetime import datetime, timezone

from pyrogram import filters
from pyrogram.errors import PeerIdInvalid, UserIsBlocked
from pyrogram.types import LinkPreviewOptions, Message, User

from app import BOT, bot

FED_BOTS_TO_QUERY = [
    609517172,  # Rose
    1376954911,  # AstrakoBot
    885745757,  #Sophie
    2059887769, #Odin
]

def safe_escape(text: str) -> str:
    escaped_text = html.escape(str(text))
    return escaped_text.replace("&#x27;", "’")
    
def parse_text_response(response: Message) -> str:
    bot_name = response.from_user.first_name
    text = response.text
    lower_text = text.lower()
    not_banned_phrases = ["no bans", "not banned", "hasn't been banned", "0 federation(s)!", "isn’t fbanned", "fbanned anywhere!"]
    if any(phrase in lower_text for phrase in not_banned_phrases):
        return f"<b>• {bot_name}:</b> Not Banned"
    else:
        return f"<b>• {bot_name}:</b> <blockquote expandable>{safe_escape(text)}</blockquote>"

async def find_latest_file_in_history(bot: BOT, chat_id: int, timeout: int = 15) -> Message | None:
    """
    Actively polls message history to find the newest file message.
    This is a robust alternative to event handlers for race conditions.
    """
    start_time = datetime.now(timezone.utc)
    while (datetime.now(timezone.utc) - start_time).total_seconds() < timeout:
        try:
            async for message in bot.get_chat_history(chat_id, limit=1):
                if message.document and message.date > start_time:
                    return message
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return None


async def query_single_bot(bot: BOT, bot_id: int, user_to_check: User) -> tuple[str, Message | None]:
    """Queries a single bot using a robust method."""
    bot_info = await bot.get_users(bot_id)
    try:
        sent_cmd = await bot.send_message(chat_id=bot_id, text=f"/fbanstat {user_to_check.id}")
        response = await sent_cmd.get_response(filters=filters.user(bot_id), timeout=20)

        if response.text and "checking" in response.text.lower():
            response = await sent_cmd.get_response(filters=filters.user(bot_id), timeout=20)

        if response.reply_markup and "Make the fedban file" in str(response.reply_markup):
            try:
                await response.click(0)
            except Exception:
                pass
                
            file_message = await find_latest_file_in_history(bot, bot_id)

            if file_message:
                result_text = f"<b>• {bot_info.first_name}:</b> Bot sent a file with the full ban list. Sending..."
            else:
                result_text = f"<b>• {bot_info.first_name}:</b> Bot was supposed to send a file, but it wasn't received (timeout)."
            return result_text, file_message
        
        elif response.text:
            return parse_text_response(response), None
        
        else:
            return f"<b>• {bot_info.first_name}:</b> <i>Received an unsupported response type.</i>", None

    except (UserIsBlocked, PeerIdInvalid):
        return f"<b>• {bot_info.first_name}:</b> <i>Bot blocked or unreachable.</i>", None
    except asyncio.TimeoutError:
        return f"<b>• {bot_info.first_name}:</b> <i>No response (timeout).</i>", None
    except Exception:
        return f"<b>• {bot_info.first_name}:</b> <i>An unknown rror occurred.</i>", None


@bot.add_cmd(cmd=["fstat", "fedstat"])
async def fed_stat_handler(bot: BOT, message: Message):
    """Checks a user's federation ban status using a robust concurrent method."""
    progress: Message = await message.reply("<code>Checking fedstat...</code>")

    target_identifier = "me"
    if message.input:
        target_identifier = message.input
    elif message.replied:
        target_identifier = message.replied.from_user.id

    try:
        user_to_check: User = await bot.get_users(target_identifier)
    except Exception as e:
        return await progress.edit(f"<b>Error:</b> Could not find the specified user.\n<code>{e}</code>", del_in=8)

    tasks = [query_single_bot(bot, bot_id, user_to_check) for bot_id in FED_BOTS_TO_QUERY]
    all_results = await asyncio.gather(*tasks)

    result_texts = []
    files_to_forward = []

    for text, file_message in all_results:
        result_texts.append(text)
        if file_message:
            files_to_forward.append(file_message)

    final_report = (
        f"<b>Federation Status for:</b> {user_to_check.mention}\n"
        f"<b>ID:</b> <code>{user_to_check.id}</code>\n\n"
        f"{'\n'.join(result_texts)}"
    )

    await progress.edit(
        final_report,
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

    for file in files_to_forward:
        await file.forward(message.chat.id)
