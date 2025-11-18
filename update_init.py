import os
import requests
from datetime import datetime

REPO_OWNER = "R0Xofficial"
REPO_NAME = "PlainUB-Extras"
REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

SCRIPT_PATH = os.path.abspath(__file__)
MODULES_DIR = os.path.dirname(os.path.dirname(SCRIPT_PATH)) if "modules" in SCRIPT_PATH else os.path.dirname(SCRIPT_PATH)
UPDATE_FILE_PATH = os.path.join(MODULES_DIR, "update.json")

def fetch_latest_commit_date_sync() -> str:
    """Pobiera z GitHub i zwraca datę ostatniego commita."""
    response = requests.get(REPO_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    pushed_at = datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC")
    return pushed_at

def initialize_version_file():
    """Sprawdza i tworzy plik update.rdm, jeśli nie istnieje."""
    if not os.path.exists(UPDATE_FILE_PATH):
        print(f"INFO: '{UPDATE_FILE_PATH}' not found. Attempting to create it on first run...")
        try:
            initial_date = fetch_latest_commit_date_sync()
            with open(UPDATE_FILE_PATH, 'w') as f:
                f.write(initial_date)
            print(f"INFO: 'update.json' created successfully with date: {initial_date}")
        except Exception as e:
            print(f"WARNING: Could not create 'update.json' on initial startup. It will be created on the first '.extupdate'. Error: {e}")

initialize_version_file()
