import os
import html
import asyncio
import uuid
from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

TEMP_DIR = "temp_codeit/"
os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_VISIBLE_DURATION = 8

LANGUAGES = {
    "python": ("Python", "py"), "py": ("Python", "py"),
    "java": ("Java", "java"),
    "c++": ("C++", "cpp"), "cpp": ("C++", "cpp"),
    "javascript": ("JavaScript", "js"), "js": ("JavaScript", "js"),
    "c#": ("C#", "cs"), "cs": ("C#", "cs"),
    "html": ("HTML", "html"),
    "kotlin": ("Kotlin", "kt"), "kt": ("Kotlin", "kt"),
    "assembly": ("Assembly", "asm"), "asm": ("Assembly", "asm"),
    "go": ("Go", "go"), "golang": ("Go", "go"),
    "rust": ("Rust", "rs"), "rs": ("Rust", "rs"),
    "swift": ("Swift", "swift"),
    "ruby": ("Ruby", "rb"), "rb": ("Ruby", "rb"),
    "php": ("PHP", "php"),
    "c": ("C", "c"),
    "brainfuck": ("Brainfuck", "bf"), "bf": ("Brainfuck", "bf"),
    "lolcode": ("LOLCODE", "lol"), "lol": ("LOLCODE", "lol"),
}

def text_to_brainfuck(text: str) -> str:
    brainfuck_code = []
    memory = [0]
    pointer = 0
    
    for char in text:
        target_value = ord(char)
        current_value = memory[pointer]
        diff = target_value - current_value
        simple_way = ('+' * diff if diff > 0 else '-' * abs(diff))
        loop_way = ""

        if abs(diff) > 10:
            factor = int(target_value**0.5)
            if factor > 1:
                remaining = target_value - (factor * factor)
                loop_code = f">{'+'*factor}[<{''.join(['+']*factor)}>-]<"
                if remaining > 0:
                    loop_code += '+' * remaining
                else:
                    loop_code += '-' * abs(remaining)
                if len(loop_code) < len(simple_way):
                    loop_way = loop_code

        if loop_way and not current_value:
             brainfuck_code.append(loop_way)
        else:
            brainfuck_code.append(simple_way)

        brainfuck_code.append('.')
        memory[pointer] = target_value
    return "".join(brainfuck_code)

def generate_code(language: str, text: str) -> str:
    """Generates a 'Hello, World!'-style program for the given language and text."""

    if language == "Brainfuck":
        return text_to_brainfuck(text)

    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    code_templates = {
        "Python": f'print("{escaped_text}")',
        "Java": f'public class Main {{\n    public static void main(String[] args) {{\n        System.out.println("{escaped_text}");\n    }}\n}}',
        "C++": f'#include <iostream>\n\nint main() {{\n    std::cout << "{escaped_text}";\n    return 0;\n}}',
        "JavaScript": f'console.log("{escaped_text}");',
        "C#": f'using System;\n\nclass Program {{\n    static void Main(string[] args) {{\n        Console.WriteLine("{escaped_text}");\n    }}\n}}',
        "HTML": f'<!DOCTYPE html>\n<html>\n<head><title>Message</title></head>\n<body>\n    <p>{html.escape(text)}</p>\n</body>\n</html>',
        "Kotlin": f'fun main() {{\n    println("{escaped_text}")\n}}',
        "Assembly": (
            'section .data\n'
            f'    msg db "{escaped_text}", 0\n\n'
            'section .text\n'
            '    global _start\n\n'
            '_start:\n'
            '    ; This is a simplified representation for Linux x86-64 NASM syntax.\n'
            '    ; It does not calculate string length dynamically.\n'
            '    mov rax, 1 ; syscall for write\n'
            '    mov rdi, 1 ; file descriptor (stdout)\n'
            '    mov rsi, msg ; message to write\n'
            '    mov rdx, 14 ; placeholder length\n'
            '    syscall\n\n'
            '    mov rax, 60 ; syscall for exit\n'
            '    xor rdi, rdi ; exit code 0\n'
            '    syscall'
        ),
        "Go": f'package main\n\nimport "fmt"\n\nfunc main() {{\n    fmt.Println("{escaped_text}")\n}}',
        "Rust": f'fn main() {{\n    println!("{escaped_text}");\n}}',
        "Swift": f'print("{escaped_text}")',
        "Ruby": f'puts "{escaped_text}"',
        "PHP": f'<?php\n\necho "{escaped_text}";\n',
        "C": f'#include <stdio.h>\n\nint main() {{\n    printf("{escaped_text}");\n    return 0;\n}}',
        "LOLCODE": (
            'HAI 1.2\n'
            f'VISIBLE "{text}"\n'
            'KTHXBYE'
        ),
    }
    return code_templates.get(language, f"// Language '{language}' not supported.")

def sync_save_code_to_file(code_string: str, file_ext: str) -> str:
    unique_id = str(uuid.uuid4())
    output_path = os.path.join(TEMP_DIR, f"main_{unique_id}.{file_ext}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code_string)
    return output_path

def safe_escape(text: str) -> str:
    return html.escape(str(text))

@bot.add_cmd(cmd="codeit")
async def codeit_handler(bot: BOT, message: Message):
    """
    CMD: CODEIT
    INFO: Turns a text message into a program file with a code preview.
    USAGE:
        .codeit [lang] (text)
        .codeit [lang] (in reply to a message)
    LANGUAGES: python, java, c++, js, cs, html, kotlin, asm, go, rust, swift, ruby, php, c, bf, lol
    """
    replied_msg = message.replied
    
    if not message.input:
        return await message.reply("<b>Usage:</b> .codeit <language> [text]", del_in=ERROR_VISIBLE_DURATION)

    parts = message.input.split(maxsplit=1)
    lang_alias = parts[0].lower()
    
    if lang_alias not in LANGUAGES:
        return await message.reply(f"Unsupported language: <code>{lang_alias}</code>.", del_in=ERROR_VISIBLE_DURATION)

    lang_name, file_ext = LANGUAGES[lang_alias]
    
    text_to_code = ""
    if len(parts) > 1:
        text_to_code = parts[1]
    elif replied_msg and replied_msg.text:
        text_to_code = replied_msg.text
    else:
        return await message.reply("Please provide text or reply to a text message.", del_in=ERROR_VISIBLE_DURATION)

    progress_message = await message.reply("<code>Generating code...</code>")
    
    output_path = ""
    temp_files = []
    try:
        code_output = generate_code(lang_name, text_to_code)
        
        output_path = await asyncio.to_thread(sync_save_code_to_file, code_output, file_ext)
        temp_files.append(output_path)
        
        preview_code = safe_escape(code_output)
        caption = f'<pre class="language-{lang_alias}">{preview_code}</pre>'
        
        if len(caption) > 1024:
            overhead_len = len(f'<pre class="language-{lang_alias}"></pre>\n... (truncated)')
            max_code_len = 1024 - overhead_len
            truncated_code = safe_escape(code_output[:max_code_len])
            caption = f'<pre class="language-{lang_alias}">{truncated_code}\n... (truncated)</pre>'
        
        reply_target = replied_msg or message
        await bot.send_document(
            chat_id=message.chat.id,
            document=output_path,
            caption=caption,
            reply_parameters=ReplyParameters(message_id=reply_target.id)
        )
        
        await progress_message.delete()

    except Exception as e:
        error_text = f"<b>Error:</b> Could not generate code.\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text, del_in=ERROR_VISIBLE_DURATION)
    finally:
        for f in temp_files:
            if f and os.path.exists(f):
                os.remove(f)
