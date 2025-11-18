import html
from pyrogram.types import Message

from app import BOT, CustomDB, Message, bot

NOTES_DB = CustomDB["NOTES"]

def safe_escape(text: str) -> str:
    return html.escape(str(text))

@bot.add_cmd(cmd=["addnote", "save"])
async def save_note_handler(bot: BOT, message: Message):
    """
    CMD: ADDNOTE / SAVE
    INFO: Saves a new note. Can save text, media, or entire messages.
    USAGE:
        .save [note_name] [text content]
        .save [note_name] (while replying to a message/media to save it)
    """
    args = message.input.split(" ", 1)
    if not args or not args[0]:
        await message.reply("You need to provide a name for the note.", del_in=5)
        return
    note_name = args[0]

    content = None
    if message.replied:
        content = message.replied.id
        await message.replied.copy("me")
    elif len(args) > 1:
        content = args[1]
    else:
        await message.reply("You need to provide content for the note or reply to a message.", del_in=5)
        return

    await NOTES_DB.add_data({"_id": note_name, "content": content})
    await message.reply(f"Note `{note_name}` saved successfully.", del_in=5)
    await message.delete()

@bot.add_cmd(cmd=["delnote", "clear"])
async def delete_note_handler(bot: BOT, message: Message):
    """
    CMD: DELNOTE / CLEAR
    INFO: Deletes a saved note.
    USAGE:
        .delnote [note_name]
    """
    note_name = message.input
    if not note_name:
        await message.reply("You need to specify which note to delete.", del_in=5)
        return

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
    """
    notes_list = []
    async for note in NOTES_DB.find():
        notes_list.append(f"• `{note['_id']}`")
    
    if not notes_list:
        await message.reply("You have no saved notes.")
        return
        
    response_text = "<b>Your saved notes:</b>\n\n" + "\n".join(notes_list)
    await message.reply(response_text)

@bot.add_cmd(cmd="get")
async def get_note_by_command(bot: BOT, message: Message):
    """
    CMD: GET
    INFO: Retrieves a saved note.
    USAGE:
        .get [note_name]
    """
    note_name = message.input
    if not note_name:
        await message.reply("You need to specify which note to get.", del_in=5)
        return

    note = await NOTES_DB.find_one({"_id": note_name})

    if not note:
        await message.reply(f"Note `{note_name}` not found.", del_in=5)
        return

    await message.delete()
    content = note["content"]

    reply_to_id = message.reply_to_message_id if message.reply_to_message else None

    if isinstance(content, int): # Content is a message ID for media
        try:
            await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id="me",
                message_id=content,
                reply_to_message_id=reply_to_id
            )
        except Exception:
            await bot.send_message(message.chat.id, "<i>Error: The saved media for this note could not be found or has been deleted from Saved Messages.</i>")
    else: # Content is text
        await bot.send_message(
            chat_id=message.chat.id,
            text=str(content),
            reply_to_message_id=reply_to_id
        )
