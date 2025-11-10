import asyncio
from asyncio import TimeoutError
import re
import json

from pyrogram import filters
from pyrogram.types import Message, User
from ub_core.utils.helpers import get_name

from app import BOT, Config, CustomDB, Message, bot, extra_config

# --- UNIVERSAL CONFIGURATION & SETUP ---
FBAN_SUDO_ID = getattr(Config, "FBAN_SUDO_ID", None)
if FBAN_SUDO_ID: FBAN_SUDO_ID = int(FBAN_SUDO_ID)
FBAN_SUDO_TRIGGER = getattr(Config, "FBAN_SUDO_TRIGGER", ".")

FED_DB = CustomDB["FED_LIST"]
BASIC_FILTER = filters.user([609517172, 2059887769, 1376954911, 885745757]) & ~filters.service
FBAN_REGEX = BASIC_FILTER & filters.regex(r"New FedBan|start.* a federation ban|FedBan Reason update.*|Would you like to update", re.IGNORECASE)
filters_in_sudo_chat = filters.chat(FBAN_SUDO_ID) if FBAN_SUDO_ID else filters.false

# --- WORKER HANDLERS (Active on ALL bots) ---

@bot.on_message(filters.command("list_my_feds", FBAN_SUDO_TRIGGER) & filters_in_sudo_chat)
async def send_feds_list_worker(bot: BOT, message: Message):
    me = await bot.get_me()
    feds = []
    async for fed in FED_DB.find():
        feds.append({"name": fed["name"], "id": fed["_id"]})
    
    response_data = {"worker_id": me.id, "worker_name": me.first_name or "Bot", "feds": feds}
    await message.reply_text(json.dumps(response_data))

@bot.on_message(filters.command("execute_fban_for", FBAN_SUDO_TRIGGER) & filters_in_sudo_chat)
async def execute_fban_remotely_worker(bot: BOT, message: Message):
    me = await bot.get_me()
    try:
        _, target_worker_id, fed_id, user_id, reason = message.text.split(" ", 4)
        if int(target_worker_id) != me.id: return
        fed_id, user_id = int(fed_id), int(user_id)
    except (ValueError, IndexError): return

    if not await FED_DB.find_one({"_id": fed_id}):
        await message.reply_text("FAILURE: Fed not found in my DB"); return

    fban_cmd = f"/fban <a href='tg://user?id={user_id}'>{user_id}</a> {reason}"
    failed = False
    try:
        cmd_msg = await bot.send_message(chat_id=fed_id, text=fban_cmd, disable_preview=True)
        response = await cmd_msg.get_response(filters=FBAN_REGEX, timeout=8)
        if not response:
             failed = True
        elif "Would you like to update this reason" in response.text:
            await response.click("Update reason")
    except Exception: failed = True
    
    await message.reply_text("SUCCESS" if not failed else "FAILURE")

# --- CONTROLLER/ORCHESTRATOR LOGIC (Triggered by user command) ---

def parse_selection(text: str, total_feds: int) -> list[int] | None:
    text = text.replace(" ", "")
    selected_indices = set()
    if "-" in text:
        parts = text.split("-");
        if len(parts) != 2 or not all(p.isdigit() for p in parts): return None
        start, end = int(parts[0]), int(parts[1])
        if not (0 < start <= end <= total_feds): return None
        return list(range(start - 1, end))
    if "," in text:
        parts = text.split(",")
        for part in parts:
            if not part.isdigit(): return None
            num = int(part)
            if not (0 < num <= total_feds): return None
            selected_indices.add(num - 1)
        return sorted(list(selected_indices))
    if text.isdigit():
        num = int(text)
        if not (0 < num <= total_feds): return None
        return [num - 1]
    return None

async def extract_selection_user_reason(message: Message):
    if not message.input: return None, None, None
    args = message.input.split()
    selection_str = args[0]
    
    user_str = ""
    reason_str = ""

    if message.replied:
        reason_str = " ".join(args[1:])
    elif len(args) >= 2:
        user_str = args[1]
        reason_str = " ".join(args[2:])
    
    if not reason_str: reason_str = "No reason specified."

    user, _ = await message.extract_user_n_reason(user_raw=user_str)
    if isinstance(user, str):
        await message.reply(user); return None, None, None
    if not isinstance(user, User):
        user_id, user_mention = user, f"<a href='tg://user?id={user}'>{user}</a>"
    else:
        user_id, user_mention = user.id, user.mention
    
    return selection_str, (user_id, user_mention, reason_str)

async def get_all_feds(bot: BOT):
    all_feds = []
    me = await bot.get_me()
    async for fed in FED_DB.find():
        all_feds.append({"name": fed["name"], "_id": fed["_id"], "owner_id": me.id, "owner_name": me.first_name or "Me"})

    if FBAN_SUDO_ID and FBAN_SUDO_TRIGGER:
        try:
            req_msg = await bot.send_message(FBAN_SUDO_ID, f"{FBAN_SUDO_TRIGGER}list_my_feds")
            await asyncio.sleep(5) 
            async for reply in bot.get_chat_history(FBAN_SUDO_ID, limit=30):
                if reply.from_user.is_self: continue
                if reply.reply_to_message_id == req_msg.id:
                    try:
                        data = json.loads(reply.text)
                        for fed in data["feds"]:
                            all_feds.append({"name": fed["name"], "_id": fed["id"], "owner_id": data["worker_id"], "owner_name": data["worker_name"]})
                    except (json.JSONDecodeError, KeyError): continue
        except Exception:
            pass
    return all_feds

@bot.add_cmd(cmd=["cfban", "cfbanp"])
async def fed_ban_orchestrator(bot: BOT, message: Message):
    if "-list" in message.flags:
        progress = await message.reply("`Gathering fed lists from all bots...`")
        all_feds = await get_all_feds(bot)
        if not all_feds: await progress.edit("No feds found on any connected account."); return
        
        output = "<b>List Of Connected Feds:</b>\n"
        for i, fed in enumerate(all_feds, 1):
            output += f"{i}. [{fed['owner_name']}] {fed['name']}\n"
        await progress.edit(output)
        return

    progress = await message.reply("❯")
    selection_str, user_info = await extract_selection_user_reason(message)
    if not selection_str or not user_info:
        await progress.edit("Invalid syntax. Use `.cfban [number] [user] [reason]` or see `.help cfban`."); return
    
    user_id, user_mention, reason = user_info
    
    if user_id in [Config.OWNER_ID, *Config.SUPERUSERS, *Config.SUDO_USERS]:
        await progress.edit("Cannot Fban Owner/Sudo users."); return

    if message.cmd == "cfbanp":
        if not message.replied: await progress.edit("Reply to a message to use it as proof."); return
        proof = await message.replied.forward(extra_config.FBAN_LOG_CHANNEL)
        reason += f"\n{ {proof.link} }"

    all_feds = await get_all_feds(bot)
    if not all_feds: await progress.edit("No feds available to ban in."); return

    selected_indices = parse_selection(selection_str, len(all_feds))
    if selected_indices is None: await progress.edit("Invalid fed selection format."); return
        
    selected_feds = [all_feds[i] for i in selected_indices]
    await progress.edit("❯❯")

    failed_feds = []
    for fed in selected_feds:
        failed = False
        try:
            req_cmd = f"{FBAN_SUDO_TRIGGER}execute_fban_for {fed['owner_id']} {fed['_id']} {user_id} {reason}"
            req_msg = await bot.send_message(FBAN_SUDO_ID, req_cmd)
            res = await req_msg.get_response(filters.user(fed["owner_id"]), 15)
            if "FAIL" in res.text: failed = True
        except Exception: failed = True

        if failed:
            failed_feds.append(f"[{fed['owner_name']}] {fed['name']}")
        await asyncio.sleep(1.5)

    total_selected, failed_count = len(selected_feds), len(failed_feds)
    if failed_feds:
        status_line = f"<b>Failed in:</b> {failed_count}/{total_selected} choosen feds"
        failed_str = "\n• " + "\n• ".join(failed_feds)
    else:
        status_line = f"<b>Status:</b> Fbanned in <b>{total_selected}</b> chosen fed(s)."
        failed_str = ""

    summary_text = (f"❯❯❯ <b>Fbanned</b> {user_mention}\n<b>ID:</b> <code>{user_id}</code>\n"
                    f"<b>Reason:</b> {reason}\n<b>Initiated in:</b> {message.chat.title or 'PM'}\n{status_line}")
    log_text = summary_text + failed_str
    if not message.is_from_owner: log_text += f"\n\n<b>By</b>: {get_name(message.from_user)}"
        
    await bot.send_message(extra_config.FBAN_LOG_CHANNEL, log_text, disable_preview=True)
    await progress.edit(summary_text, del_in=8, disable_preview=True)
