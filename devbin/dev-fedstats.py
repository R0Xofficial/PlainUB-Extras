import asyncio
import html
from datetime import datetime, timezone
from pyrogram import filters
from pyrogram.errors import PeerIdInvalid, UserIsBlocked
from pyrogram.types import LinkPreviewOptions, Message, User

from app import BOT, bot

FED_BOTS_TO_QUERY = [609517172, 1376954911, 885745757, 2059887769]

def safe_escape(text: str) -> str:
    return html.escape(str(text)) if text else ""
    
def parse_text_response(response: Message) -> str:
    bot_name = response.from_user.first_name
    text = response.text or ""
    lower_text = text.lower()
    not_banned_phrases = ["no bans", "not banned", "hasn't been banned", "0 federation(s)!", "isn’t fbanned", "fbanned anywhere!"]
    if any(phrase in lower_text for phrase in not_banned_phrases):
        return f"<b>• {bot_name}:</b> Not Banned"
    return f"<b>• {bot_name}:</b> <blockquote expandable>{safe_escape(text)}</blockquote>"

async def await_bot_response(bot: BOT, chat_id: int, start_time: datetime, timeout: int = 15) -> Message | None:
    """Actively polls message history to find the newest message from the bot."""
    try:
        async def check_history():
            while True:
                async for message in bot.get_chat_history(chat_id, limit=5):
                    if message.from_user and message.from_user.id == chat_id and message.date > start_time:
                        return message
                await asyncio.sleep(1)
        return await asyncio.wait_for(check_history(), timeout=timeout)
    except asyncio.TimeoutError:
        return None

async def query_single_bot(bot: BOT, bot_id: int, user_to_check: User) -> tuple[str, Message | None]:
    bot_info = await bot.get_users(bot_id)
    bot_name = bot_info.first_name
    try:
        start_time = datetime.now(timezone.utc)
        await bot.send_message(chat_id=bot_id, text=f"/fbanstat {user_to_check.id}")
        
        response = await await_bot_response(bot, bot_id, start_time)

        if not response:
            raise asyncio.TimeoutError

        if response.text and "checking" in response.text.lower():
            start_time = datetime.now(timezone.utc)
            response = await await_bot_response(bot, bot_id, start_time)
            if not response: raise asyncio.TimeoutError
        
        if response.reply_markup and "Make the fedban file" in str(response.reply_markup):
            try:
                await response.click(0)
            except Exception: pass
            
            start_time = datetime.now(timezone.utc)
            file_message = await await_bot_response(bot, bot_id, start_time)

            if file_message and file_message.document:
                return f"<b>• {bot_name}:</b> Bot sent a file with the full ban list.", file_message
            return f"<b>• {bot_name}:</b> Bot was supposed to send a file, but it wasn't received.", None

        if response.text:
            return parse_text_response(response), None
        
        return f"<b>• {bot_name}:</b> <i>Received an unsupported response type.</i>", None

    except (UserIsBlocked, PeerIdInvalid):
        return f"<b>• {bot_name}:</b> <i>Bot blocked or unreachable.</i>", None
    except asyncio.TimeoutError:
        return f"<b>• {bot_name}:</b> <i>No response (timeout).</i>", None
    except Exception:
        return f"<b>• {bot_name}:</b> <i>An unknown error occurred.</i>", None

@bot.add_cmd(cmd=["dfstat", "dfedstat"])
async def fed_stat_handler(bot: BOT, message: Message):
    """
    WARNING: Its a dev version of this module. Its can not work!!!
    CMD: DFSTAT / DFEDSTAT
    INFO: Checks a user's federation ban status across multiple federations.
    USAGE:
        .dfstat [user_id/@username/reply]
    """
    progress: Message = await message.reply("<code>Checking federation status...</code>")

    target_identifier = "me"
    if message.input:
        target_identifier = message.input
    elif message.replied and message.replied.from_user:
        target_identifier = message.replied.from_user.id

    try:
        user_to_check: User = await bot.get_users(target_identifier)
    except Exception as e:
        return await progress.edit(f"<b>Error:</b> Could not find the specified user.\n<code>{safe_escape(str(e))}</code>", del_in=8)

    tasks = [query_single_bot(bot, bot_id, user_to_check) for bot_id in FED_BOTS_TO_QUERY]
    all_results = await asyncio.gather(*tasks)

    result_texts = [text for text, _ in all_results]
    files_to_forward = [file_msg for _, file_msg in all_results if file_msg]

    final_report = (
        f"<b>Federation Status for:</b> {user_to_check.mention}\n"
        f"<b>User ID:</b> <code>{user_to_check.id}</code>\n\n"
        f"{'\n'.join(result_texts)}"
    )

    await progress.edit(final_report, link_preview_options=LinkPreviewOptions(is_disabled=True))

    if files_to_forward:
        for file in files_to_forward:
            await file.forward(message.chat.id)
