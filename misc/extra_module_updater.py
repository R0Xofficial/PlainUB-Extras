import os
import asyncio
import requests
from datetime import datetime

from ub_core.utils import run_shell_cmd
from app import BOT, Message

REPO_OWNER = "R0Xofficial"
REPO_NAME = "PlainUB-Extras"
REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

APP_DIR = os.path.join(os.getcwd(), "app")
MODULES_DIR = os.path.join(APP_DIR, "modules")
UPDATE_FILE_PATH = os.path.join(MODULES_DIR, "update.json")

def fetch_latest_commit_date_sync() -> str:
    response = requests.get(REPO_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    pushed_at = datetime.strptime(data['pushed_at'], "%Y-%m-%dTH:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC")
    return pushed_at

@BOT.add_cmd(cmd="extupdate", allow_sudo=False)
async def extra_modules_updater(bot: BOT, message: Message):
    """
    CMD: EXT UPDATE
    INFO: Updates external modules if installed
    """
    output = await run_shell_cmd(cmd=f"cd {MODULES_DIR} && git pull", timeout=10)

    update_successful = "Already up to date." not in output.strip() and "error" not in output.lower()
    
    if update_successful:
        try:
            latest_commit_date = await asyncio.to_thread(fetch_latest_commit_date_sync)
            with open(UPDATE_FILE_PATH, 'w') as f:
                f.write(latest_commit_date)
        except Exception:
            pass

    await message.reply(f"<pre language=shell>{output}</pre>")

    if update_successful:
        bot.raise_sigint()
