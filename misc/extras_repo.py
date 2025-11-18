import os
import html
import asyncio
import requests
from datetime import datetime
from pyrogram.types import Message, LinkPreviewOptions, ReplyParameters

from app import BOT, bot

REPO_OWNER = "R0Xofficial"
REPO_NAME = "PlainUB-Extras"
REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"

PLAIN_UB_URL = "https://github.com/thedragonsinn/plain-ub"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
BOT_ROOT = os.path.dirname(os.path.dirname(MODULES_DIR))
BACKGROUND_IMAGE_PATH = os.path.join(BOT_ROOT, "assets", "dark.png")
UPDATE_FILE_PATH = os.path.join(MODULES_DIR, "update.json")

def fetch_repo_data_sync() -> dict:
    response = requests.get(REPO_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    pushed_at = datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC")

    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "issues": data.get("open_issues_count", 0),
        "last_commit_date": pushed_at,
    }

def get_local_version_date() -> str:
    if not os.path.exists(UPDATE_FILE_PATH):
        return "Not Found"
    try:
        with open(UPDATE_FILE_PATH, 'r') as f:
            local_date = f.read().strip()
            return local_date if local_date else "Empty"
    except Exception:
        return "Error Reading File"

@bot.add_cmd(cmd=["modrepo", "mods"])
async def repo_handler(bot: BOT, message: Message):
    progress_msg = await message.reply("<code>Fetching repository information and checking update...</code>")
    
    try:
        repo_data = await asyncio.to_thread(fetch_repo_data_sync)
        local_date = get_local_version_date()
        
        remote_date = repo_data['last_commit_date']
        
        if local_date == remote_date:
            status_text = "✅ Up to date"
        elif local_date in ["Not Found", "Empty", "Error Reading File"]:
            status_text = f"❓ Unknown ({local_date})"
        else:
            status_text = "⚠️ Update available!"

        status_line = f" › Status : <code>{status_text}</code>"

        caption = (
            f"<a href='{REPO_URL}'><b>PlainUB-Extras</b></a>, additional modules and features designed for use with "
            f"<a href='{PLAIN_UB_URL}'>Plain-UB</a>.\n\n"
            f" › Stars : <code>{repo_data['stars']}</code>\n"
            f" › Forks : <code>{repo_data['forks']}</code>\n"
            f" › Open Issues : <code>{repo_data['issues']}</code>\n"
            f" › Last Commit : <code>{remote_date}</code>\n"
            f" › Your Version : <code>{local_date}</code>\n\n"
            f"{status_line}"
        )

        if not os.path.exists(BACKGROUND_IMAGE_PATH):
            await progress_msg.edit(caption, link_preview_options=LinkPreviewOptions(is_disabled=True))
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
