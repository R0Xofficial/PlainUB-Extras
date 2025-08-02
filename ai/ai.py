import os
import html
import asyncio
import requests
from pyrogram.types import Message, ReplyParameters
from dotenv import load_dotenv

from app import BOT, bot

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(MODULES_DIR, "extra_config.env")
load_dotenv(dotenv_path=ENV_PATH)
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ERROR_VISIBLE_DURATION = 15

@bot.add_cmd(cmd="ask")
async def ask_handler(bot: BOT, message: Message):
    """
    CMD: ASK
    INFO: Asks a question to the Llama 3 AI model on Cloudflare.
    USAGE:
        .ask [question]
        .ask (in reply to a message to use its text as context)
    """
    if not CF_ACCOUNT_ID or not CF_API_TOKEN or "YOUR_KEY" in CF_API_TOKEN:
        return await message.reply("<b>Cloudflare AI not configured.</b>", del_in=ERROR_VISIBLE_DURATION)

    prompt = message.input
    display_prompt = prompt
    if message.replied and message.replied.text:
        replied_text = message.replied.text
        if prompt:
            display_prompt = f"(In reply to text) {prompt}"
            prompt = f"Based on the following text:\n---\n{replied_text}\n---\nAnswer this question: {prompt}"
        else:
            display_prompt = "(Summarizing replied text)"
            prompt = f"Summarize or analyze the following text:\n{replied_text}"

    if not prompt: return await message.reply("<b>Usage:</b> .ask [question]", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply("<code>Thinking...</code>")
    try:
        api_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/meta/llama-3-8b-instruct"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
        payload = {
            "messages": [{"role": "system", "content": "You are a helpful AI assistant."}, {"role": "user", "content": prompt}],
            "max_tokens": 2048 
        }
        
        response = await asyncio.to_thread(requests.post, api_url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        response_data = response.json()
        
        if response_data.get("success"):
            ai_response = response_data["result"]["response"].strip()
            
            final_output = (
                f"<b>Prompt:</b> <i>{html.escape(display_prompt)}</i>\n\n"
                f"<pre language=llama3>{html.escape(ai_response)}</pre>"
            )
            
            await bot.send_message(
                chat_id=message.chat.id, text=final_output,
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            
            await progress_message.delete(); await message.delete()
        else:
            raise Exception(f"API Error: {response_data.get('errors') or 'Unknown error'}")

    except requests.exceptions.Timeout:
         await progress_message.edit("<b>Error:</b> The request to the AI timed out.", del_in=ERROR_VISIBLE_DURATION)
    except Exception as e:
        # If the message is too long for Telegram, this will catch the error.
        await progress_message.edit(f"<b>Error:</b> Could not get a response.\n<code>{html.escape(str(e))}</code>", del_in=ERROR_VISIBLE_DURATION)
