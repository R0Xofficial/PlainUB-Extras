import asyncio
from asyncio import TimeoutError
import re

from pyrogram import filters
from pyrogram.types import Message, User
from ub_core.utils.helpers import get_name

from app import BOT, Config, CustomDB, Message, bot, extra_config

FED_DB = CustomDB["FED_LIST"]

BASIC_FILTER = filters.user([609517172, 2059887769, 1376954911, 885745757]) & ~filters.service
FBAN_REGEX = BASIC_FILTER & filters.regex(
    r"(New FedBan|starting a federation ban|start a federation ban|FedBan Reason update|FedBan reason updated|Would you like to update this reason)",
    re.IGNORECASE,
)

def parse_selection(text: str, total_feds: int) -> list[int] | None:
    text = text.replace(" ", "")
    selected_indices = set()

    if "-" in text:
        parts = text.split("-")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            return None
        start, end = int(parts[0]), int(parts[1])
        if not (0 < start <= end <= total_feds):
            return None
        return list(range(start - 1, end))
    
    if "," in text:
        parts = text.split(",")
        for part in parts:
            if not part.isdigit():
                return None
            num = int(part)
            if not (0 < num <= total_feds):
                return None
            selected_indices.add(num - 1)
        return sorted(list(selected_indices))

    if text.isdigit():
        num = int(text)
        if not (0 < num <= total_feds):
            return None
        return [num - 1]

    return None

async def get_user_reason(message: Message, progress: Message) -> tuple[int, str, str] | None:
    user, reason = await message.extract_user_n_reason()
    if isinstance(user, str):
        await progress.edit(user)
        return None
    if not isinstance(user, User):
        user_id = user
        user_mention = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    else:
        user_id = user.id
        user_mention = user.mention
    return user_id, user_mention, reason

async def _choose_and_perform_fed_ban(bot: BOT, message: Message, with_proof: bool):
    progress = await message.reply("❯")

    extracted_info = await get_user_reason(message=message, progress=progress)
    if not extracted_info:
        return

    user_id, user_mention, reason = extracted_info

    if user_id in [Config.OWNER_ID, *Config.SUPERUSERS, *Config.SUDO_USERS]:
        await progress.edit("Cannot Fban Owner/Sudo users.")
        return

    if with_proof:
        if not message.replied:
            await progress.edit("Reply to a message to use it as proof.")
            return
        proof = await message.replied.forward(extra_config.FBAN_LOG_CHANNEL)
        reason += f"\n{ {proof.link} }"

    feds = []
    output = "<b>List Of Connected Feds:</b>\n"
    i = 1
    async for fed in FED_DB.find():
        feds.append(fed)
        output += f"{i}. {fed['name']}\n"
        i += 1

    if not feds:
        await progress.edit("You don't have any Feds Connected.")
        return

    output += "\nReply with number, range (e.g. 1-5), or list (e.g. 1,3,5).\nType `cancel` to abort."
    await progress.edit(output)

    try:
        choice_msg = await progress.get_response(
            filters=filters.user(message.from_user.id), timeout=90
        )
    except TimeoutError:
        await progress.edit("Timeout. No choice was made.", del_in=5)
        return

    try:
        await choice_msg.delete()
    except Exception:
        pass

    if choice_msg.text and choice_msg.text.lower() == "cancel":
        await progress.edit("`Cancelled.`", del_in=5)
        return

    selected_indices = parse_selection(choice_msg.text, len(feds))

    if selected_indices is None:
        await progress.edit("Invalid selection format.", del_in=5)
        return
        
    selected_feds = [feds[i] for i in selected_indices]
    
    await progress.edit("❯❯")

    fban_cmd = f"/fban <a href='tg://user?id={user_id}'>{user_id}</a> {reason}"
    failed_feds = []

    for fed in selected_feds:
        try:
            cmd_msg = await bot.send_message(
                chat_id=fed["_id"], text=fban_cmd, disable_preview=True
            )
            response = await cmd_msg.get_response(filters=FBAN_REGEX, timeout=8)
            if not response:
                failed_feds.append(fed["name"])
            elif "Would you like to update this reason" in response.text:
                await response.click("Update reason")
        except Exception as e:
            await bot.log_text(
                text=f"An Error occurred while fbanning in chosen fed: {fed['name']} [{fed['_id']}]\nError: {e}",
                type="CFBAN_ERROR",
            )
            failed_feds.append(fed["name"])
        await asyncio.sleep(1)
    
    total_selected = len(selected_feds)
    failed_str = ""
    if failed_feds:
        status_line = f"<b>Failed in:</b> {len(failed_feds)}/{total_selected} chosen feds."
        failed_str = "\n• " + "\n• ".join(failed_feds)
    else:
        status_line = f"<b>Status:</b> Fbanned in <b>{total_selected}</b> chosen fed(s)."

    summary_text = (
        f"❯❯❯ <b>Fbanned</b> {user_mention}\n"
        f"<b>ID:</b> <code>{user_id}</code>\n"
        f"<b>Reason:</b> {reason}\n"
        f"<b>Initiated in:</b> {message.chat.title or 'PM'}\n"
        f"{status_line}"
    )

    log_text = summary_text
    if failed_str:
        log_text += failed_str

    if not message.is_from_owner:
        log_text += f"\n\n<b>By</b>: {get_name(message.from_user)}"
        
    await bot.send_message(
        chat_id=extra_config.FBAN_LOG_CHANNEL, text=log_text, disable_preview=True
    )
    
    await progress.edit(summary_text, del_in=8, disable_preview=True)

@bot.add_cmd(cmd="cfban")
async def choose_fed_ban(bot: BOT, message: Message):
    await _choose_and_perform_fed_ban(bot, message, with_proof=False)

@bot.add_cmd(cmd="cfbanp")
async def choose_fed_ban_proof(bot: BOT, message: Message):
    await _choose_and_perform_fed_ban(bot, message, with_proof=True)
