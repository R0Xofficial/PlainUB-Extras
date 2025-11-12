import asyncio

from pyrogram.enums import ChatType
from pyrogram.types import Chat, User
from ub_core.utils.helpers import get_name

from app import BOT, Config, CustomDB, Message, bot, extra_config

GBAN_TASK_LOCK = asyncio.Lock()

GBAN_DB = CustomDB["GBAN_CHAT_LIST"]


@bot.add_cmd(cmd="addg")
async def add_gban_chat(bot: BOT, message: Message):
    """
    CMD: ADDG
    INFO: Adds a chat to the GBAN list.
    USAGE:
        .addg | .addg NAME
    """
    data = dict(name=message.input or message.chat.title, type=str(message.chat.type))
    await GBAN_DB.add_data({"_id": message.chat.id, **data})
    text = f"#GBANS\n<b>{data['name']}</b>: <code>{message.chat.id}</code> added to the GBAN bot chat list."
    await message.reply(text=text, del_in=5, block=True)
    await bot.log_text(text=text, type="info")


@bot.add_cmd(cmd="delg")
async def remove_gban_chat(bot: BOT, message: Message):
    """
    CMD: DELG
    INFO: Removes a bot chat from the GBAN list.
    FLAGS: -all to delete all gban bot chats.
    USAGE:
        .delg | .delg id | .delg -all
    """
    if "-all" in message.flags:
        await GBAN_DB.drop()
        await message.reply("GBAN bot chat list cleared.")
        return

    chat: int | str | Chat = message.input or message.chat
    name = ""

    if isinstance(chat, Chat):
        name = f"Bot Chat: {chat.title}\n"
        chat = chat.id
    elif chat.lstrip("-").isdigit():
        chat = int(chat)

    deleted: int = await GBAN_DB.delete_data(id=chat)

    if deleted:
        text = f"#GBANS\n<b>{name}</b><code>{chat}</code> removed from the GBAN bot chat list."
        await message.reply(text=text, del_in=8)
        await bot.log_text(text=text, type="info")
    else:
        await message.reply(text=f"<b>{name or chat}</b> is not in the GBAN bot chat list.", del_in=8)


@bot.add_cmd(cmd="listg")
async def gban_chat_list(bot: BOT, message: Message):
    """
    CMD: LISTG
    INFO: Displays the connected GBAN bot chats.
    FLAGS: -id to list Gban Chat IDs.
    USAGE: .listg | .listg -id
    """
    output: str = ""
    total = 0

    async for gban_chat in GBAN_DB.find():
        output += f'<b>• {gban_chat["name"]}</b>\n'

        if "-id" in message.flags:
            output += f'  <code>{gban_chat["_id"]}</code>\n'

        total += 1

    if not total:
        await message.reply("You don't have any bot chats connected to GBAN.")
        return

    output: str = f"List of <b>{total}</b> connected GBAN bot chats:\n\n{output}"
    await message.reply(output, del_in=30, block=True)


@bot.add_cmd(cmd=["gban", "gbanp"])
async def gban_user(bot: BOT, message: Message):
    """
    CMD: GBAN / GBANP
    INFO: Globall ban user in connected bots to your userbot.
    USAGE:
        .gban [ID/Username/reply] [reason] (Globall ban user)
        .gbanp [reply] [reason] (Globall ban user with proof)
    """
    progress: Message = await message.reply("❯")
    extracted_info = await get_user_reason(message=message, progress=progress)
    if not extracted_info:
        await progress.edit("Failed to extract user info.")
        return

    user_id, user_mention, reason = extracted_info

    if user_id in [Config.OWNER_ID, *Config.SUPERUSERS, *Config.SUDO_USERS]:
        await progress.edit("Cannot gban the owner or sudo users.")
        return

    proof_str: str = ""
    if message.cmd == "gbanp":
        if not message.replied:
            await progress.edit("Reply to a message with the proof.")
            return
        proof = await message.replied.forward(extra_config.FBAN_LOG_CHANNEL)
        proof_str = f"\n{ {proof.link} }"

    reason = f"{reason}{proof_str}"

    if message.replied and message.chat.type != ChatType.PRIVATE:
        try:
            if message.chat._raw.admin_rights:
                await message.replied.reply(
                    text=f"!dban {reason}", disable_preview=True, del_in=3, block=False
                )
        except UserNotParticipant:
            pass

    gban_cmd: str = f"/gban <a href='tg://user?id={user_id}'>{user_id}</a> {reason}"

    await perform_gban_task(
        user_id=user_id,
        user_mention=user_mention,
        command=gban_cmd,
        task_type="Gban",
        reason=reason,
        progress=progress,
        message=message,
    )


@bot.add_cmd(cmd="ungban")
async def un_gban_user(bot: BOT, message: Message):
    progress: Message = await message.reply("❯")
    extracted_info = await get_user_reason(message=message, progress=progress)

    if not extracted_info:
        await progress.edit("Failed to extract user info.")
        return

    user_id, user_mention, reason = extracted_info
    ungban_cmd: str = f"/ungban <a href='tg://user?id={user_id}'>{user_id}</a> {reason}"

    await perform_gban_task(
        user_id=user_id,
        user_mention=user_mention,
        command=ungban_cmd,
        task_type="Un-Gban",
        reason=reason,
        progress=progress,
        message=message,
    )


async def get_user_reason(message: Message, progress: Message) -> tuple[int, str, str] | None:
    user, reason = await message.extract_user_n_reason()
    if isinstance(user, str):
        await progress.edit(user)
        return
    if not isinstance(user, User):
        user_id = user
        user_mention = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    else:
        user_id = user.id
        user_mention = user.mention
    return user_id, user_mention, reason


async def perform_gban_task(
    user_id: int,
    user_mention: str,
    command: str,
    task_type: str,
    reason: str,
    progress: Message,
    message: Message,
):
    async with GBAN_TASK_LOCK:
        await progress.edit("❯❯")

        total: int = 0
        failed: list[str] = []
        success_count: int = 0

        async for gban_chat in GBAN_DB.find():
            chat_id = int(gban_chat["_id"])
            total += 1

            try:
                await bot.send_message(chat_id=chat_id, text=command, disable_preview=True)
                success_count += 1
            except Exception as e:
                await bot.log_text(
                    text=f"Error while sending gban command to bot chat: {gban_chat['name']} [{chat_id}]"
                    f"\nError: {e}",
                    type="GBAN_ERROR",
                )
                failed.append(gban_chat["name"])
                continue

            await asyncio.sleep(1)

        if not total:
            await progress.edit("You don't have any bot chats on the GBAN list! Use `.addg` to add one.")
            return

        action_past_tense = task_type.replace("-", "") + "ned"

        resp_str = (
            f"❯❯❯ <b>{action_past_tense}</b> {user_mention}"
            f"\n<b>ID</b>: {user_id}"
            f"\n<b>Reason</b>: {reason}"
            f"\n<b>Initiated in</b>: {message.chat.title or 'PM'}"
        )

        if failed:
            resp_str += f"\n<b>Failed</b> in: {len(failed)}/{total}\n• " + "\n• ".join(failed)
        else:
            resp_str += f"\n<b>Status</b>: {action_past_tense} in <b>{total}</b> bots."

        if not message.is_from_owner:
            resp_str += f"\n\n<b>By</b>: {get_name(message.from_user)}"

        await bot.send_message(
            chat_id=extra_config.FBAN_LOG_CHANNEL, text=resp_str, disable_preview=True
        )

        await progress.edit(text=resp_str, del_in=5, block=True, disable_preview=True)
