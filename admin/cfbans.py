import asyncio
import re

from pyrogram import filters
from pyrogram.errors import TimeoutError
from pyrogram.types import Message, User
from ub_core.utils.helpers import get_name

from app import BOT, Config, CustomDB, Message, bot, extra_config

FED_DB = CustomDB["FED_LIST"]

BASIC_FILTER = filters.user([609517172, 2059887769, 1376954911, 885745757]) & ~filters.service
FBAN_REGEX = BASIC_FILTER & filters.regex(
    r"(New FedBan|starting a federation ban|start a federation ban|FedBan Reason update|FedBan reason updated|Would you like to update this reason)",
    re.IGNORECASE,
)

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

    output += "\nReply with the number of the fed you want to ban in."
    await progress.edit(output)

    try:
        choice_msg = await progress.get_response(
            filters=filters.user(message.from_user.id), timeout=60
        )
    except TimeoutError:
        await progress.edit("Timeout. No choice was made.", del_in=5)
        return

    if not choice_msg.text or not choice_msg.text.isdigit():
        await progress.edit("Invalid choice. Please provide a number.", del_in=5)
        return
    
    choice = int(choice_msg.text)
    if not 0 < choice <= len(feds):
        await progress.edit("Invalid number. Please choose from the list.", del_in=5)
        return

    chosen_fed = feds[choice - 1]
    await progress.edit(f"❯❯")

    fban_cmd = f"/fban <a href='tg://user?id={user_id}'>{user_id}</a> {reason}"
    failed = False

    try:
        cmd_msg = await bot.send_message(
            chat_id=chosen_fed["_id"], text=fban_cmd, disable_preview=True
        )
        response = await cmd_msg.get_response(filters=FBAN_REGEX, timeout=8)
        if not response:
            failed = True
        elif "Would you like to update this reason" in response.text:
            await response.click("Update reason")
    except Exception as e:
        await bot.log_text(
            text=f"An Error occurred while fbanning in chosen fed: {chosen_fed['name']} [{chosen_fed['_id']}]\nError: {e}",
            type="CFBAN_ERROR",
        )
        failed = True
    
    if failed:
        status_line = f"<b>Failed in:</b> {chosen_fed['name']}"
    else:
        status_line = f"<b>Status:</b> Fbanned in {chosen_fed['name']}"

    log_text = (
        f"❯❯❯ <b>Fbanned</b> {user_mention}\n"
        f"<b>ID:</b> <code>{user_id}</code>\n"
        f"<b>Reason:</b> {reason}\n"
        f"<b>Initiated in:</b> {message.chat.title or 'PM'}\n"
        f"{status_line}"
    )

    if not message.is_from_owner:
        log_text += f"\n\n<b>By</b>: {get_name(message.from_user)}"
        
    await bot.send_message(
        chat_id=extra_config.FBAN_LOG_CHANNEL, text=log_text, disable_preview=True
    )
    
    await progress.edit(log_text, del_in=5, disable_preview=True)

@bot.add_cmd(cmd="cfban")
async def choose_fed_ban(bot: BOT, message: Message):
    await _choose_and_perform_fed_ban(bot, message, with_proof=False)

@bot.add_cmd(cmd="cfbanp")
async def choose_fed_ban_proof(bot: BOT, message: Message):
    await _choose_and_perform_fed_ban(bot, message, with_proof=True)
