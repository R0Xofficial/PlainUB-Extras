import asyncio
from asyncio import TimeoutError
import re

from pyrogram import filters
from pyrogram.types import Message, User
from ub_core.utils.helpers import get_name

from app import BOT, Config, CustomDB, Message, bot, extra_config

FED_DB = CustomDB["FED_LIST"]

BASIC_FILTER = filters.user([609517172, 2059887769, 1376954911, 885745757]) & ~filters.service
FBAN_REGEX = BASIC_FILTER & filters.regex(r"New FedBan|start.* a federation ban|FedBan Reason update.*|Would you like to update", re.IGNORECASE)
UNFBAN_REGEX = BASIC_FILTER & filters.regex(r"New un-FedBan|I'll give|Un-FedBan", re.IGNORECASE)

def parse_selection(text: str, total_feds: int) -> list[int] | None:
    text = text.replace(" ", "")
    selected_indices = set()
    if "-" in text:
        parts = text.split("-")
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

async def get_user_reason(message: Message, progress: Message) -> tuple[int, str, str] | None:
    user, reason = await message.extract_user_n_reason()
    
    if not reason:
        reason = "None"

    if isinstance(user, str):
        await progress.edit(user)
        return None
    if not isinstance(user, User):
        user_id, user_mention = user, f"<a href='tg://user?id={user}'>{user}</a>"
    else:
        user_id, user_mention = user.id, user.mention
    return user_id, user_mention, reason

async def _choose_and_perform_fed_action(bot: BOT, message: Message, with_proof: bool, action: str):
    progress = await message.reply("❯")

    extracted_info = await get_user_reason(message=message, progress=progress)
    if not extracted_info: return

    user_id, user_mention, reason = extracted_info

    if user_id in [Config.OWNER_ID, *Config.SUPERUSERS, *Config.SUDO_USERS] and action == "fban":
        await progress.edit("Cannot Fban Owner/Sudo users."); return

    if with_proof:
        if not message.replied: await progress.edit("Reply to a message to use it as proof."); return
        proof = await message.replied.forward(extra_config.FBAN_LOG_CHANNEL)
        if reason == "None":
             reason = f"Proof Attached.\n{ {proof.link} }"
        else:
             reason += f"\n{ {proof.link} }"

    feds = []
    output = "<b>List Of Connected Feds:</b>\n"
    i = 1
    async for fed in FED_DB.find():
        feds.append(fed); output += f"{i}. {fed['name']}\n"; i += 1

    if not feds: await progress.edit("You don't have any Feds Connected."); return

    output += f"\nReply to this message with number, range (7-12), or list (1,2,8) to {action}.\nType `cancel` to abort."
    await progress.edit(output)

    try:
        response_filter = filters.user(message.from_user.id) & filters.create(
            lambda _, __, msg: msg.reply_to_message_id == progress.id
        )
        choice_msg = await progress.get_response(filters=response_filter, timeout=90)
    except TimeoutError:
        await progress.edit("Timeout.", del_in=5)
        return

    try: await choice_msg.delete()
    except Exception: pass

    if choice_msg.text and choice_msg.text.lower() == "cancel": await progress.edit("`Cancelled.`", del_in=5); return

    selected_indices = parse_selection(choice_msg.text, len(feds))
    if selected_indices is None: await progress.edit("Invalid selection.", del_in=5); return
        
    selected_feds = [feds[i] for i in selected_indices]
    await progress.edit("❯❯")

    cmd_text = f"/{action} <a href='tg://user?id={user_id}'>{user_id}</a> {reason}"
    task_filter = FBAN_REGEX if action == "fban" else UNFBAN_REGEX
    failed_feds = []

    for fed in selected_feds:
        try:
            cmd_msg = await bot.send_message(fed["_id"], cmd_text, disable_preview=True)
            response = await cmd_msg.get_response(filters=task_filter, timeout=8)
            if not response: failed_feds.append(fed["name"])
            elif "Would you like to update" in response.text: await response.click("Update reason")
        except Exception as e:
            await bot.log_text(f"Error during {action} in {fed['name']}: {e}", type=f"C{action.upper()}_ERROR")
            failed_feds.append(fed["name"])
        await asyncio.sleep(1)
    
    total_selected = len(selected_feds)
    action_past_tense = "Fbanned" if action == "fban" else "Un-Fbanned"
    failed_str = ""

    if failed_feds:
        status_line = f"<b>Failed</b> in: {len(failed_feds)}/{total_selected} chosen feds."
        failed_str = "\n• " + "\n• ".join(failed_feds)
    else:
        status_line = f"<b>Status:</b> {action_past_tense} in <b>{total_selected}</b> chosen fed(s)."

    summary_text = (f"❯❯❯ <b>{action_past_tense}</b> {user_mention}\n"
                    f"<b>ID:</b> {user_id}\n"
                    f"<b>Reason:</b> {reason}\n"
                    f"<b>Initiated in:</b> {message.chat.title or 'PM'}\n"
                    f"{status_line}")
    log_text = summary_text
    if failed_str: log_text += failed_str

    if not message.is_from_owner: log_text += f"\n\n<b>By</b>: {get_name(message.from_user)}"
        
    await bot.send_message(extra_config.FBAN_LOG_CHANNEL, log_text, disable_preview=True)
    await progress.edit(summary_text, del_in=8, disable_preview=True)

@bot.add_cmd(cmd="cfban")
async def choose_fed_ban(bot: BOT, message: Message):
    """
    CMD: CFBAN / CFBANP
    INFO:
        Initiates a selective fed-ban.
        Instead of banning in all connected feds,
        this command will present a numbered list
        of federations for you to choose from.

    USAGE:
        .cfban(p) [uid | @ | reply to message] [reason]
    """
    await _choose_and_perform_fed_action(bot, message, with_proof=False, action="fban")

@bot.add_cmd(cmd="cfbanp")
async def choose_fed_ban_proof(bot: BOT, message: Message):
    """
    CMD: CFBAN / CFBANP
    INFO:
        Initiates a selective fed-ban.
        Instead of banning in all connected feds,
        this command will present a numbered list
        of federations for you to choose from.

    USAGE:
        .cfban(p) [uid | @ | reply to message] [reason]
    """
    await _choose_and_perform_fed_action(bot, message, with_proof=True, action="fban")

@bot.add_cmd(cmd="uncfban")
async def choose_fed_unban(bot: BOT, message: Message):
    """
    CMD: CUNFBAN
    INFO:
        Initiates a selective un-fedban.
        This command works exactly like `cfban`,
        presenting a list of federations to choose 
        from for the unban action.

    USAGE:
        .cunfban [uid | @ | reply to message] [reason]
    """
    await _choose_and_perform_fed_action(bot, message, with_proof=False, action="unfban")
