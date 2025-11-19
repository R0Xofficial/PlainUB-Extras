import os
import html
from dotenv import load_dotenv
from pyrogram.types import Message, User

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BOT_ROOT = os.path.dirname(APP_DIR)

CONFIG_ENV_PATH = os.path.join(BOT_ROOT, "config.env")

if os.path.exists(CONFIG_ENV_PATH):
    load_dotenv(dotenv_path=CONFIG_ENV_PATH)

LOG_CHAT_STR = os.getenv("LOG_CHAT")
LOG_CHAT = int(LOG_CHAT_STR) if LOG_CHAT_STR and LOG_CHAT_STR.strip() else None

@bot.add_cmd(cmd=["block", "unblock"])
async def block_unblock_handler(bot: BOT, message: Message):
    user_to_act_on: User = None

    try:
        if message.input:
            identifier = message.input.strip()
            user_to_act_on = await bot.get_users(identifier)
        elif message.replied and message.replied.from_user:
            user_to_act_on = message.replied.from_user
        else:
            await message.reply("<b>Usage:</b> Reply to a user or provide their ID/@username.", del_in=MEDIUM_TIMEOUT)
            return
            
        if not user_to_act_on:
            raise ValueError("Could not find the specified user.")

        if message.cmd == "block":
            action = bot.block_user
            log_tag = "#BLOCK"
            action_str = "has been blocked."
        else:
            action = bot.unblock_user
            log_tag = "#UNBLOCK"
            action_str = "has been unblocked."

        await action(user_to_act_on.id)
        
        if LOG_CHAT:
            log_text = (
                f"{log_tag}\n"
                f"{user_to_act_on.mention} [`{user_to_act_on.id}`] {action_str}"
            )
            try:
                await bot.send_message(chat_id=LOG_CHAT, text=log_text, parse_mode=None)
            except Exception:
                pass

    except Exception as e:
        await message.reply(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LARGE_TIMEOUT)
