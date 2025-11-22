import os
import html
import asyncio
import requests
from datetime import datetime

from ub_core.utils import run_shell_cmd
from app import BOT, Message

from app.modules.settings import REPO_OWNER, REPO_NAME, TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

APP_DIR = os.path.join(os.getcwd(), "app")
MODULES_DIR = os.path.join(APP_DIR, "modules")
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
            return f.read().strip() or "Empty"
    except Exception:
        return "Error Reading File"

@BOT.add_cmd(cmd=["extupdate", "eupdate", "eup"], allow_sudo=False)
async def unified_update_handler(bot: BOT, message: Message):
    """
    CMD: EXTUPDATE / EUPDATE / EUP
    INFO: Checks for or pulls updates for external modules.
    FLAGS:
        -pull: Pulls the latest changes from the repository and restarts userbot.
    USAGE:
        .extupdate (Checks for available updates)
        .extupdate -pull (Pulls and applies updates)
    """

    if "-pull" in message.flags:
        output = await run_shell_cmd(cmd=f"cd {MODULES_DIR} && git pull", timeout=10)
        await message.reply(f"<pre language=shell>{output}</pre>")
        if output.strip() != "Already up to date.":
            bot.raise_sigint()
        return

    progress_msg = await message.reply("<code>Checking for updates...</code>")
    try:
        remote_date = await asyncio.to_thread(fetch_latest_commit_date_sync)
        local_date = get_local_version_date()
        
        if local_date == remote_date:
            # status_emoji = "✅"
            status_text = "<b>You are up to date!</b>"
        elif local_date in ["Not Found", "Empty", "Error Reading File"]:
            # status_emoji = "❓"
            status_text = f"<b>Could not determine local version.</b>\nReason: <code>{local_date}</code>"
        else:
            # status_emoji = "⚠️"
            status_text = f"<b>A new update is available!</b>\n<i>Run the command with the <code>-pull</code> flag to apply updates.</i>"

        response_text = (
            f"{status_text}\n\n"
            f"<b>Upstream Repo:</b> <code>{REPO_OWNER}</code>/<code>{REPO_NAME}</code>\n\n"
            f"<b>Latest Version:</b>\n<code>{remote_date}</code>\n\n"
            f"<b>Your Version:</b>\n<code>{local_date}</code>"
        )
        
        await progress_msg.edit(response_text)

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LARGE_TIMEOUT)
