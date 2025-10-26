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
    885745757,  # Sophie
    2059887769, # Odin
]

def safe_escape(text: str) -> str:
    """Safely escapes HTML text while preserving readability."""
    escaped_text = html.escape(str(text))
    return escaped_text.replace("&#x27;", "’")
    
def parse_text_response(response: Message) -> str:
    """Formats the text response from a federation bot."""
    bot_name = response.from_user.first_name
    text = response.text
    lower_text = text.lower()
    not_banned_phrases = ["no bans", "not banned", "hasn't been banned", "0 federation(s)!", "isn’t fbanned", "fbanned anywhere!"]
    if any(phrase in lower_text for phrase in not_banned_phrases):
        return f"<b>• {bot_name}:</b> Not Banned"
    else:
        return f"<b>• {bot_name}:</b> <blockquote expandable>{safe_escape(text)}</blockquote>"

# The find_latest_file_in_history function has been removed as it was unreliable.
# The query_single_bot function below now uses a much more robust method.

async def query_single_bot(bot: BOT, bot_id: int, user_to_check: User) -> tuple[str, Message | None]:
    """
    Queries a single bot using the reliable bot.listen() method.
    This resolves the issue with files sent by bots like Rose being missed.
    """
    bot_info = await bot.get_users(bot_id)
    try:
        # Step 1: Send the command to the bot
        await bot.send_message(chat_id=bot_id, text=f"/fbanstat {user_to_check.id}")

        # Step 2: Wait for the first response from the bot (could be "checking..." or the result)
        response = await bot.listen(chat_id=bot_id, filters=filters.user(bot_id), timeout=20)

        # Step 3: If the bot first sends "checking...", wait for the second, actual response
        if response.text and "checking" in response.text.lower():
            response = await bot.listen(chat_id=bot_id, filters=filters.user(bot_id), timeout=20)
        
        # Step 4: Check if the response contains a button to generate a file
        if response.reply_markup and "Make the fedban file" in str(response.reply_markup):
            try:
                # Click the button to request the file
                await response.click(0)
                
                # STEP 5 (THE KEY FIX):
                # Use bot.listen with a document filter to wait for the file message.
                # This is much more reliable than polling the message history.
                file_message = await bot.listen(
                    chat_id=bot_id,
                    filters=filters.user(bot_id) & filters.document,
                    timeout=25  # Give the bot a bit more time to generate and send the file
                )

                result_text = f"<b>• {bot_info.first_name}:</b> The bot sent a file with the full ban list. Forwarding..."
                return result_text, file_message

            except asyncio.TimeoutError:
                # This error will occur if the bot doesn't send the file within the timeout after the click
                result_text = f"<b>• {bot_info.first_name}:</b> The bot was supposed to send a file, but it wasn't received (timeout)."
                return result_text, None
            except Exception:
                # Other potential errors during file retrieval
                return f"<b>• {bot_info.first_name}:</b> <i>An error occurred while trying to retrieve the file.</i>", None

        # Step 6: If the response is plain text, parse it
        elif response.text:
            return parse_text_response(response), None
        
        # Step 7: Handle any other unexpected response type
        else:
            return f"<b>• {bot_info.first_name}:</b> <i>Received an unsupported response type.</i>", None

    except (UserIsBlocked, PeerIdInvalid):
        return f"<b>• {bot_info.first_name}:</b> <i>The bot is blocked or unreachable.</i>", None
    except asyncio.TimeoutError:
        # This error will occur if the bot doesn't respond to the initial command at all
        return f"<b>• {bot_info.first_name}:</b> <i>No response (timeout).</i>", None
    except Exception:
        return f"<b>• {bot_info.first_name}:</b> <i>An unknown error occurred.</i>", None


@bot.add_cmd(cmd=["dfstat", "dfedstat"])
async def fed_stat_handler(bot: BOT, message: Message):
    """
    WARNING: Its a dev version of this module. Its can not work!!!
    CMD: DFSTAT / DFEDSTAT
    INFO: Checks a user's federation ban status across multiple federations.
    USAGE:
        .dfstat [user_id/@username/reply]
    """
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

    # Run queries for all bots concurrently
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
        f"<b>User ID:</b> <code>{user_to_check.id}</code>\n\n"
        f"{'\n'.join(result_texts)}"
    )

    await progress.edit(
        final_report,
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

    # Forward all collected files
    for file in files_to_forward:
        await file.forward(message.chat.id)
