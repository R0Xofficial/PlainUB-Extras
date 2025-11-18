import os
import html
import asyncio
import requests
import uuid
from pyrogram.types import Message, ReplyParameters
from dotenv import load_dotenv

from app import BOT, bot

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.dirname(SCRIPT_DIR)
ENV_PATH = os.path.join(MODULES_DIR, "extra_config.env")
load_dotenv(dotenv_path=ENV_PATH)
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
TEMP_DIR = "temp_codegen/"
os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_VISIBLE_DURATION = 15

LANGUAGE_EXTENSIONS = {
    "python": "py", "py": "py",
    "javascript": "js", "js": "js",
    "typescript": "ts", "ts": "ts",
    "java": "java",
    "c++": "cpp", "cpp": "cpp",
    "c#": "cs", "cs": "cs",
    "c": "c",
    "go": "go", "golang": "go",
    "rust": "rs", "rs": "rs",
    "kotlin": "kt", "kt": "kt",
    "swift": "swift",
    "php": "php",
    "ruby": "rb", "rb": "rb",
    "html": "html",
    "css": "css",
    "json": "json",
    "xml": "xml",
    "sql": "sql",
    "shell": "sh", "bash": "sh", "sh": "sh",
    "powershell": "ps1", "ps1": "ps1",
    "assembly": "asm", "asm": "asm",
}

def sync_save_code_to_file(code_string: str, file_ext: str) -> str:
    """Saves the code string to a unique temporary file and returns the path."""
    unique_id = str(uuid.uuid4())
    output_path = os.path.join(TEMP_DIR, f"code_{unique_id}.{file_ext}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code_string)
    return output_path

@bot.add_cmd(cmd=["codegen", "cg"])
async def codegen_handler(bot: BOT, message: Message):
    """
    CMD: CODEGEN / CG
    INFO: Generates code based on a natural language prompt using Cloudflare's Code Llama.
    USAGE:
        .codegen [language] (description of the code)
    EXAMPLE:
        .codegen python a function to calculate fibonacci sequence
    """
    if not CF_ACCOUNT_ID or not CF_API_TOKEN or "YOUR_KEY" in CF_API_TOKEN:
        return await message.reply("<b>Cloudflare AI not configured.</b>", del_in=ERROR_VISIBLE_DURATION)
    if not message.input:
        return await message.reply("<b>Usage:</b> .codegen [language] (description)", del_in=ERROR_VISIBLE_DURATION)
    
    parts = message.input.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Please specify both a language and a description.", del_in=ERROR_VISIBLE_DURATION)
        
    language = parts[0].lower()
    prompt = parts[1]

    progress_message = await message.reply("<code>Generating...</code>")
    
    output_path = ""
    temp_files = []
    try:
        api_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@hf/thebloke/codellama-7b-instruct-awq"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
        
        full_prompt = f"In {language}, write a professional code that does the following: {prompt}. Only output the raw code, without any explanation or markdown formatting."
        payload = {"prompt": full_prompt}
        
        response = await asyncio.to_thread(requests.post, api_url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        response_data = response.json()
        
        if response_data.get("success"):
            generated_code = response_data["result"]["response"].strip()
            
            if "```" in generated_code:
                try:
                    code_block = generated_code.split("```")[1]
                    if code_block.lower().startswith(language.split()[0]):
                        code_block = '\n'.join(code_block.split('\n')[1:])
                    generated_code = code_block.strip()
                except IndexError:
                    pass

            file_extension = LANGUAGE_EXTENSIONS.get(language, "txt")
            
            output_path = await asyncio.to_thread(sync_save_code_to_file, generated_code, file_extension)
            temp_files.append(output_path)
            
            await bot.send_document(
                chat_id=message.chat.id,
                document=output_path,
                caption=f"<b>Prompt:</b> <i>{html.escape(prompt)}</i>",
                reply_parameters=ReplyParameters(message_id=message.id)
            )
            
            await progress_message.delete()
        else:
            raise Exception(f"API Error: {response_data.get('errors') or 'Unknown error'}")

    except Exception as e:
        error_text = f"<b>Error:</b> Could not generate code.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
