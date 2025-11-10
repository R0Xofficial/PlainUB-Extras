import random
from pyrogram.types import Message, User

from app import BOT, Config, Message, bot

SLAP_TEXTS = [
    "{slapper} slaps {slappee} around a bit with a large trout.",
    "{slapper} gives {slappee} a swift slap.",
    "{slapper} throws a wet noodle at {slappee}.",
    "{slapper} slaps {slappee} with a book, yelling 'Study this!'",
    "{slapper} unleashes a flurry of a thousand slaps upon {slappee}.",
    "{slapper} smacks {slappee} with the power of a thousand angry keyboards.",
    "{slapper} pokes {slappee} in the eye. Oops, wrong command.",
    "{slapper} calmly slaps {slappee}. Nothing personal.",
    "{slapper} trips and accidentally slaps {slappee} on the way down.",
    "{slapper} downloads a slap.exe and runs it on {slappee}.",
    "{slapper} rolls up a newspaper and gives {slappee} a light smack.",
    "{slapper} challenges {slappee} to a slap duel and wins instantly.",
    "{slapper} uses their stand, 「ZA HANDO」, to slap {slappee} across dimensions.",
    "{slapper} slaps {slappee} with a fresh slice of pizza.",
    "{slapper} sends a high-voltage static shock through their keyboard to slap {slappee}.",
]

@bot.add_cmd(cmd="slap")
async def slap_handler(bot: BOT, message: Message):
    slapper = message.from_user.mention
    slappee = slapper
    target_user = None

    if message.replied:
        target_user = message.replied.from_user
    elif message.input:
        try:
            target_user = await bot.get_users(message.input)
        except Exception:
            slappee = message.input
    
    if isinstance(target_user, User):
        slappee = target_user.mention

    try:
        slap_text = random.choice(SLAP_TEXTS)
        final_text = slap_text.format(slapper=slapper, slappee=slappee)
    except Exception as e:
        final_text = f"{slapper} tried to slap {slappee}, but something went wrong: {e}"

    await bot.send_message(
        chat_id=message.chat.id,
        text=final_text,
        reply_to_message_id=message.replied_id if message.replied else None
    )
    await message.delete()```
