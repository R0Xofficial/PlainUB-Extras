import os
import html
import asyncio
import requests
from pyrogram.types import Message, ReplyParameters
from dotenv import load_dotenv

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(MODULES_DIR, "extra_config.env")
load_dotenv(dotenv_path=ENV_PATH)
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
MODEL = os.getenv("TEXT_AI")

@bot.add_cmd(cmd="ask")
async def ask_handler(bot: BOT, message: Message):
    """
    CMD: ASK
    INFO: Asks a question to the AI model from Cloudflare.
    USAGE:
        .ask [question]
        .ask (in reply to a message to use its text as context)
    """
    if not MODEL or MODEL.strip() == "":
        return await message.reply("<b>Cloudflare Text Model AI not configured.</b>", del_in=LONG_TIMEOUT)
    
    if not CF_ACCOUNT_ID or not CF_API_TOKEN or "YOUR_KEY" in CF_API_TOKEN:
        return await message.reply("<b>Cloudflare API or Account ID not configured.</b>", del_in=LONG_TIMEOUT)

    prompt = message.input
    display_prompt = prompt
    if message.replied and message.replied.text:
        replied_text = message.replied.text
        if prompt:
            display_prompt = f"{prompt}"
            prompt = f"{replied_text}\n\n\n{prompt}"
        else:
            display_prompt = "-"
            prompt = f"{replied_text}"
            
    if not prompt: return await message.reply("<b>Usage:</b> .ask [question]", del_in=MEDIUM_TIMEOUT)

    progress_message = await message.reply("<code>Thinking...</code>")
    try:
        api_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messages": [{"role": "system", "content": "You are a helpful AI assistant."}, {"role": "user", "content": prompt}],
            "max_tokens": 2048 
        }
        
        response = await asyncio.to_thread(requests.post, api_url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        response_data = response.json()
        
        if response_data.get("success"):
            ai_response = response_data["result"]["response"].strip()

            model_short_name = MODEL.split("/")[-1] 
            
            final_output = (
                f"<b>Prompt:</b> <i>{html.escape(display_prompt)}</i>\n"
                f"<pre language={model_short_name}>{html.escape(ai_response)}</pre>"
            )
            
            if message.replied:
                await bot.send_message(
                    chat_id=message.chat.id, text=final_output,
                    reply_parameters=ReplyParameters(message_id=message.replied.id)
                )
                await progress_message.delete()
            else:
                await progress_message.edit(
                    text=final_output
                )
            
        else:
            await progress_message.edit(f"API Error: {response_data.get('errors') or 'Unknown error'}", del_in=LONG_TIMEOUT)

    except requests.exceptions.Timeout:
         await progress_message.edit("<b>Error:</b> The request to the AI timed out.", del_in=LONG_TIMEOUT)
    except Exception as e:
        await progress_message.edit(f"<b>Error:</b> Could not get a response.\n<code>{html.escape(str(e))}</code>", del_in=LONG_TIMEOUT)
