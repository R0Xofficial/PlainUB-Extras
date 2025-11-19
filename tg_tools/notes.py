import html
from pyrogram.types import Message, ReplyParameters

from app import BOT, Config, CustomDB, Message, bot

NOTES_DB = CustomDB["NOTES"]
MEDIA_STORAGE_CHANNEL = getattr(Config, "LOG_CHAT", None)
if MEDIA_STORAGE_CHANNEL:
    MEDIA_STORAGE_CHANNEL = int(MEDIA_STORAGE_CHANNEL)

def safe_escape(text: str) -> str:
    return html.escape(str(text))

@bot.add_cmd(cmd=["addnote", "save"])
async def save_note_handler(bot: BOT, message: Message):
    """
    CMD: ADDNOTE / SAVE
    INFO: Saves a new note. Note names are case-insensitive.
    USAGE:
        .save [note_name] [text content]
        .save [note_name] (while replying to a message/media to save it)
    """
    if not MEDIA_STORAGE_CHANNEL and message.replied:
        await message.reply("To save media, you must set `LOG_CHAT` in your config.", del_in=8)
        return

    args = message.input.split(" ", 1)
    if not args or not args[0]:
        await message.reply("You need to provide a name for the note.", del_in=5); return
    
    note_name = args[0].lower()

    content = None
    if message.replied:
        forwarded_message = await message.replied.forward(MEDIA_STORAGE_CHANNEL)
        content = forwarded_message.id
    elif len(args) > 1:
        content = args[1]
    else:
        await message.reply("You need to provide content for the note or reply to a message.", del_in=5); return

    await NOTES_DB.add_data({"_id": note_name, "content": content})
    await message.reply(f"Note `{note_name}` saved successfully.", del_in=5)

@bot.add_cmd(cmd=["delnote", "clear"])
async def delete_note_handler(bot: BOT, message: Message):
    """
    CMD: DELNOTE / CLEAR
    INFO: Deletes a saved note. Note names are case-insensitive.
    USAGE:
        .delnote [note_name]
    """
    note_name = message.input
    if not note_name:
        await message.reply("You need to specify which note to delete.", del_in=5); return

    note_name = note_name.lower()
    deleted = await NOTES_DB.delete_data(id=note_name)
    if deleted:
        await message.reply(f"Note `{note_name}` has been deleted.", del_in=5)
    else:
        await message.reply(f"Note `{note_name}` not found.", del_in=5)

@bot.add_cmd(cmd="notes")
async def list_notes_handler(bot: BOT, message: Message):
    """
    CMD: NOTES
    INFO: Lists all saved notes.
    USAGE:
        .notes
    """
    notes_list = []
    async for note in NOTES_DB.find():
        notes_list.append(f"• `{note['_id']}`")
    
    if not notes_list:
        await message.reply("You have no saved notes."); return
        
    response_text = "<b>Your saved notes:</b>\n\n" + "\n".join(notes_list)
    await message.reply(response_text)

@bot.add_cmd(cmd="get")
async def get_note_by_command(bot: BOT, message: Message):
    """
    CMD: GET
    INFO: Retrieves a saved note. Note names are case-insensitive.
    USAGE:
        .get [note_name]
    """
    note_name = message.input
    if not note_name:
        await message.reply("You need to specify which note to get.", del_in=5); return

    note_name = note_name.lower()
    note = await NOTES_DB.find_one({"_id": note_name})
    if not note:
        await message.reply(f"Note `{note_name}` not found.", del_in=5); return

    await message.delete()
    content = note["content"]

    reply_params = None
    if message.reply_to_message:
        reply_params = ReplyParameters(message_id=message.reply_to_message.id)

    if isinstance(content, int):
        if not MEDIA_STORAGE_CHANNEL:
            await bot.send_message(message.chat.id, "<i>Error: `LOG_CHAT` is not configured, cannot retrieve media note.</i>"); return
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=MEDIA_STORAGE_CHANNEL,
                message_id=content,
                reply_parameters=reply_params
            )
        except Exception:
            await bot.send_message(message.chat.id, "<i>Error: The saved media for this note could not be found on the log channel. It might have been deleted.</i>")
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=str(content),
            reply_parameters=reply_params,
            disable_web_page_preview=True
        )
