import os
import html
import asyncio
import hashlib
import requests
import re
import base64
from pyrogram.types import Message, LinkPreviewOptions, ReplyParameters
from dotenv import load_dotenv

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(MODULES_DIR, "extra_config.env")
load_dotenv(dotenv_path=ENV_PATH)

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

TEMP_DIR = "temp_virustotal/"
os.makedirs(TEMP_DIR, exist_ok=True)
VT_API_URL = "https://www.virustotal.com/api/v3"


def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_url(text: str) -> bool: return text.lower().startswith(("http://", "https://"))
def is_ip(text: str) -> bool: return bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", text))
def is_domain(text: str) -> bool: return "." in text and "/" not in text and not is_ip(text)

def format_vt_report(data: dict, scan_type: str, resource_id: str, original_input: str = "") -> str:
    if scan_type == "file":
        header = "<b>VirusTotal File Report:</b>"
    else:
        header = f"<b>VirusTotal Report for {scan_type.capitalize()}:</b>\n<code>{html.escape(original_input)}</code>"
    report_lines = [header]
    stats = data.get("last_analysis_stats", {})
    malicious = stats.get("malicious", 0); suspicious = stats.get("suspicious", 0)
    detections = malicious + suspicious
    total_scans = sum(stats.values())
    report_lines.append(f"<b>  - Detections:</b> <code>{detections} / {total_scans}</code>")
    if malicious > 0: report_lines.append("<b>  - Status:</b> 🔴 Malicious")
    elif suspicious > 0: report_lines.append("<b>  - Status:</b> 🟠 Suspicious")
    else: report_lines.append("<b>  - Status:</b> 🟢 Clean")
    if scan_type == "file": report_lines.append(f"<b>  - Type:</b> <code>{data.get('type_description', 'N/A')}</code>")
    if detections > 0:
        results = data.get("last_analysis_results", {})
        detection_details = [f"    - {engine}: <code>{html.escape(result['result'])}</code>" for engine, result in results.items() if result["category"] in ["malicious", "suspicious"]]
        if detection_details:
            report_lines.append("\n<b>Detection Details:</b>"); report_lines.append(f"<blockquote expandable>{'\n'.join(detection_details)}</blockquote>")
    gui_path = f"{scan_type}/{resource_id}"
    if scan_type == "ip": gui_path = f"ip-address/{resource_id}"
    report_lines.append(f"\n<a href='https://www.virustotal.com/gui/{gui_path}'>View Full Report</a>")
    return "\n".join(report_lines)

@bot.add_cmd(cmd=["virustotal", "vt"])
async def virustotal_handler(bot: BOT, message: Message):
    if not VIRUSTOTAL_API_KEY or VIRUSTOTAL_API_KEY == "TUTAJ_WKLEJ_SWOJ_KLUCZ_API":
        return await message.reply("<b>VirusTotal API Key not configured.</b>", del_in=LONG_TIMEOUT)
    api_key = VIRUSTOTAL_API_KEY
    if message.replied and message.replied.media: await scan_file(api_key, message)
    elif message.input:
        if is_url(message.input): await scan_url(api_key, message)
        elif is_ip(message.input): await scan_domain_or_ip(api_key, message, "ip")
        elif is_domain(message.input): await scan_domain_or_ip(api_key, message, "domain")
        else: await message.reply("Invalid input.", del_in=LONG_TIMEOUT)
    else: await message.reply("Reply to a file or provide a URL/domain/IP.", del_in=MEDIUM_TIMEOUT)

async def scan_file(api_key: str, message: Message):
    progress = await message.reply("<code>Downloading...</code>")
    original_path = ""
    temp_files = []
    try:
        original_path = await bot.download_media(message.replied, file_name=os.path.join(TEMP_DIR, ""))
        temp_files.append(original_path)
        await progress.edit("<code>Calculating hash...</code>")
        file_hash = await asyncio.to_thread(calculate_sha256, original_path)
        await progress.edit("<code>Querying VirusTotal...</code>")
        headers = {"x-apikey": api_key}; url = f"{VT_API_URL}/files/{file_hash}"
        response = await asyncio.to_thread(requests.get, url, headers=headers)
        if response.status_code == 200: final_report = format_vt_report(response.json()["data"]["attributes"], "file", file_hash)
        elif response.status_code == 404: final_report = "<b>VirusTotal Report:</b>\n<b>  - Status:</b> ⚪ Not in database."
        else: final_report = f"<b>VirusTotal Report:</b>\n<b>  - Error:</b> API code {response.status_code}."
        await bot.send_message(message.chat.id, final_report, reply_parameters=ReplyParameters(message_id=message.replied.id), link_preview_options=LinkPreviewOptions(is_disabled=True))
        await progress.delete(); await message.delete()
    except Exception as e:
        await progress.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
    finally:
        for f in temp_files:
            if f and os.path.exists(f): os.remove(f)

async def scan_url(api_key: str, message: Message):
    progress = await message.reply("<code>Querying URL...</code>")
    try:
        target_url = message.input
        url_id = base64.urlsafe_b64encode(target_url.encode()).decode().strip("=")
        headers = {"x-apikey": api_key}; url = f"{VT_API_URL}/urls/{url_id}"
        response = await asyncio.to_thread(requests.get, url, headers=headers)
        if response.status_code == 200: final_report = format_vt_report(response.json()["data"]["attributes"], "url", url_id, target_url)
        elif response.status_code == 404:
            final_report = f"<b>VirusTotal Report for URL:</b>\n<code>{html.escape(target_url)}</code>\n<b>  - Status:</b> ⚪ Not in database. Submitting..."
            post_url = f"{VT_API_URL}/urls"; post_data = {"url": target_url}
            await asyncio.to_thread(requests.post, post_url, data=post_data, headers=headers)
            final_report += "\n<i>  Check the report in a minute.</i>"
        else: final_report = f"<b>VirusTotal Report:</b>\n<b>  - Error:</b> API code {response.status_code}."
        await progress.edit(final_report, link_preview_options=LinkPreviewOptions(is_disabled=True))
        await message.delete() # Delete the original command
    except Exception as e:
        await progress.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)

async def scan_domain_or_ip(api_key: str, message: Message, scan_type: str):
    progress = await message.reply(f"<code>Querying {scan_type.capitalize()}...</code>")
    try:
        resource = message.input
        endpoint = "ip_addresses" if scan_type == "ip" else "domains"
        headers = {"x-apikey": api_key}; url = f"{VT_API_URL}/{endpoint}/{resource}"
        response = await asyncio.to_thread(requests.get, url, headers=headers)
        if response.status_code == 200: final_report = format_vt_report(response.json()["data"]["attributes"], scan_type, resource, resource)
        elif response.status_code == 404: final_report = f"<b>VirusTotal Report:</b>\n<b>  - Status:</b> ⚪ {scan_type.capitalize()} not found."
        else: final_report = f"<b>VirusTotal Report:</b>\n<b>  - Error:</b> API code {response.status_code}."
        await progress.edit(final_report, link_preview_options=LinkPreviewOptions(is_disabled=True))
    except Exception as e:
        await progress.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
