import os
import asyncio
import requests
from datetime import datetime

REPO_OWNER = "R0Xofficial"
REPO_NAME = "PlainUB-Extras"
REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

SCRIPT_PATH = os.path.abspath(__file__)
if "modules" in SCRIPT_PATH:
    MODULES_DIR = os.path.dirname(os.path.dirname(SCRIPT_PATH))
else:
    MODULES_DIR = os.path.dirname(SCRIPT_PATH)
UPDATE_FILE_PATH = os.path.join(MODULES_DIR, "update.json")

def fetch_latest_commit_date_sync() -> str:
    """Pobiera z GitHub i zwraca datę ostatniego commita."""
    response = requests.get(REPO_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    pushed_at = datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC")
    return pushed_at

async def initialize_version_file():
    await asyncio.sleep(15)

    if not os.path.exists(UPDATE_FILE_PATH):
        print(f"INFO: 'update.json' not found. Creating it in the background...")
        try:
            initial_date = await asyncio.to_thread(fetch_latest_commit_date_sync)
            with open(UPDATE_FILE_PATH, 'w') as f:
                f.write(initial_date)
            print(f"INFO: 'update.json' created successfully with date: {initial_date}")
        except Exception as e:
            print(f"WARNING: Background task could not create 'update.json'. Error: {e}")

asyncio.create_task(initialize_version_file())
