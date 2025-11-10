import random
from pyrogram.types import Message, User

from app import BOT, Config, Message, bot

SLAP_TEXTS = [
    "{slapper} installs SLAP v2.0 and executes it on {slappee} with maximum efficiency 💥",
    "{slapper} slaps {slappee} so hard, their Wi-Fi disconnects.",
    "{slapper} uploads a 500GB slap.zip directly to {slappee}'s face.",
    "{slapper} pings {slappee} with /slap — latency: 0ms, damage: 9999.",
    "{slapper} slaps {slappee} using pure JavaScript — no framework, no mercy.",
    "{slapper} throws {slappee} into /dev/null and calls it a day.",
    "{slapper} smacks {slappee} with a keyboard screaming '404: Respect not found!'",
    "{slapper} launches a tactical slap drone targeting {slappee}... hit confirmed 🎯",
    "{slapper} slaps {slappee} so hard, even Clippy asks if they need help.",
    "{slapper} imports 'slap' from chaos.py and executes it flawlessly on {slappee}.",
    "{slapper} slaps {slappee} with a freshly baked baguette of justice 🥖",
    "{slapper} performs a full system reboot on {slappee} via open-palm protocol.",
    "{slapper} activates turbo slap mode — {slappee} can’t alt+F4 fast enough.",
    "{slapper} slaps {slappee} so hard their cookies get deleted 🍪",
    "{slapper} uses slap.exe — critical hit! {slappee} is now experiencing lag IRL.",
    "{slapper} sends {slappee} a slap.mp4 — 4K, 60FPS, Dolby Surround.",
    "{slapper} throws {slappee} into the recycle bin and empties it 💀",
    "{slapper} slaps {slappee} with the power of a corrupted Windows update.",
    "{slapper} just ran 'sudo slap {slappee}' and got admin privileges.",
    "{slapper} activates anime mode — *\"Nani?!\"* — {slappee} gets slapped across 3 dimensions.",
    "{slapper} connects to {slappee}’s Bluetooth just to send a virtual slap.",
    "{slapper} slaps {slappee} so hard their antivirus flags it as a trojan.",
    "{slapper} spawns a Minecraft piston and smacks {slappee} into the void.",
    "{slapper} downloads extra RAM just to slap {slappee} faster.",
    "{slapper} slaps {slappee} so hard their Google search history gets wiped.",
    "{slapper} summons a BSOD just to slap {slappee} with the sound of despair.",
    "{slapper} slaps {slappee} using only binary code — 01010011 01001100 01000001 01010000!",
    "{slapper} hacks into the matrix and inserts one legendary slap on {slappee}.",
    "{slapper} launches an orbital slap strike — {slappee} is now a crater.",
    "{slapper} slaps {slappee} so hard their phone autocorrects pain to '{slapper}'.",
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
        reply_to_message_id=message.replied.id if message.replied else None
    )
    await message.delete()
