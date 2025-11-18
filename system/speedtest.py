import asyncio
import html
import re
from pyrogram.types import Message

from app import BOT, bot

ERROR_VISIBLE_DURATION = 8

async def run_command(command: str) -> tuple[str, str, int]:
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    return (
        stdout.decode('utf-8', errors='replace').strip(),
        stderr.decode('utf-8', errors='replace').strip(),
        process.returncode
    )


@bot.add_cmd(cmd="speedtest")
async def speedtest_handler(bot: BOT, message: Message):
    """
    CMD: SPEEDTEST
    INFO: Runs a speedtest to check internet connection speed.
    USAGE: .speedtest
    """
    
    progress_message = await message.reply("<code>Running speedtest...</code>")
    
    command = "speedtest --simple"
    
    try:
        stdout, stderr, returncode = await run_command(command)
        
        if returncode == 0 and "Cannot" not in stdout:

            ping = re.search(r"Ping:\s(.*?)\s", stdout)
            download = re.search(r"Download:\s(.*?)\s", stdout)
            upload = re.search(r"Upload:\s(.*?)\s", stdout)

            ping_res = ping.group(1) if ping else "N/A"
            download_res = download.group(1) if download else "N/A"
            upload_res = upload.group(1) if upload else "N/A"

            final_text = (
                f"<b>🚀 Speedtest Results:</b>\n\n"
                f"<b>Ping:</b> <code>{ping_res} ms</code>\n"
                f"<b>Download:</b> <code>{download_res} Mbit/s</code>\n"
                f"<b>Upload:</b> <code>{upload_res} Mbit/s</code>"
            )
            
            await progress_message.edit(final_text)
            await message.delete()

        else:
            error_details = stderr or stdout or "Unknown error."
            raise RuntimeError(error_details)

    except Exception as e:
        error_text = f"<b>Error:</b> Speedtest failed.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
