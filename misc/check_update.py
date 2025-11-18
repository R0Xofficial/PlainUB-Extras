import os
import html
import asyncio
import requests
from datetime import datetime
from pyrogram.types import Message, LinkPreviewOptions

from app import BOT, bot

REPO_OWNER = "R0Xofficial"
REPO_NAME = "PlainUB-Extras"
REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
UPDATE_FILE_PATH = os.path.join(MODULES_DIR, "update.json")

def fetch_latest_commit_date_sync() -> str:
    response = requests.get(REPO_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    pushed_at = datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC")
    return pushed_at

def get_local_version_date() -> str:
    if not os.path.exists(UPDATE_FILE_PATH):
        return "Not Found"
    try:
        with open(UPDATE_FILE_PATH, 'r') as f:
            local_date = f.read().strip()
            return local_date if local_date else "Empty"
    except Exception:
        return "Error Reading File"

@bot.add_cmd(cmd=["checkupdate", "cupdate"])
async def check_update_handler(bot: BOT, message: Message):
    progress_msg = await message.reply("<code>Checking for updates...</code>")
    
    try:
        remote_date = await asyncio.to_thread(fetch_latest_commit_date_sync)
        local_date = get_local_version_date()
        
        if local_date == remote_date:
            status_emoji = "✅"
            status_text = "<b>You are up to date!</b>"
        elif local_date in ["Not Found", "Empty", "Error Reading File"]:
            status_emoji = "❓"
            status_text = f"<b>Could not determine local version.</b>\nReason: <code>{local_date}</code>"
        else:
            status_emoji = "⚠️"
            status_text = f"<b>A new update is available!</b>\nUse `extupdate` command to update {REPO_NAME}"
        
        response_text = (
            f"{status_emoji} {status_text}\n\n"
            f"<b>Latest Version:</b>\n<code>{remote_date}</code>\n\n"
            f"<b>Your Version:</b>\n<code>{local_date}</code>"
        )
        
        await progress_msg.edit(response_text)

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=15)
