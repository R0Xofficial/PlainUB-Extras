import os
import html
import asyncio
import requests
from datetime import datetime
from pyrogram.types import Message, LinkPreviewOptions, ReplyParameters

from app import BOT, bot

from app.modules.repo import REPO_OWNER, REPO_NAME

REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"

PLAIN_UB_URL = "https://github.com/thedragonsinn/plain-ub"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
BOT_ROOT = os.path.dirname(os.path.dirname(MODULES_DIR))
BACKGROUND_IMAGE_PATH = os.path.join(BOT_ROOT, "assets", "dark.png")

def fetch_repo_data_sync() -> dict:
    response = requests.get(REPO_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    pushed_at = datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "issues": data.get("open_issues_count", 0),
        "last_commit_date": pushed_at,
    }

@bot.add_cmd(cmd=["modrepo", "mods"])
async def repo_handler(bot: BOT, message: Message):
    """
    CMD: MODREPO / MODS
    INFO: Shows an info card for the PlainUB-Extras repository.
    USAGE:
        .mods
    """
    progress_msg = await message.reply("<code>Fetching repository information...</code>")
    
    try:
        repo_data = await asyncio.to_thread(fetch_repo_data_sync)
        
        caption = (
            f"<a href='{REPO_URL}'><b>PlainUB-Extras</b></a>, additional modules and features designed for use with "
            f"<a href='{PLAIN_UB_URL}'>Plain-UB</a>.\n\n"
            f" › Stars : <code>{repo_data['stars']}</code>\n"
            f" › Forks : <code>{repo_data['forks']}</code>\n"
            f" › Open Issues : <code>{repo_data['issues']}</code>\n"
            f" › Last Commit : <code>{repo_data['last_commit_date']}</code>"
        )

        if not os.path.exists(BACKGROUND_IMAGE_PATH):
            await progress_msg.edit(caption, link_preview_options=LinkPreviewOptions(is_disabled=True))
            await message.delete()
            return

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=BACKGROUND_IMAGE_PATH,
            caption=caption,
            reply_parameters=ReplyParameters(message_id=message.id),
        )
        
        await progress_msg.delete()
        await message.delete()

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=15)
