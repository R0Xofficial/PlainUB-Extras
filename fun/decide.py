import random
from pyrogram.types import Message

from app import BOT, bot

from app.modules.settings import TINY_TIMEOUT, SMALL_TIMEOUT, MEDIUM_TIMEOUT, LONG_TIMEOUT, VERY_LONG_TIMEOUT, LARGE_TIMEOUT

DECIDE_RESPONSES = [
    "Yes, definitely.", "No, absolutely not.", "Maybe, think about it.",
    "The answer is unclear, try again.", "Go for it!", "I wouldn't recommend it.",
    "Signs point to yes.", "Don't count on it.", "Without a doubt.", "My sources say no.",
]

@bot.add_cmd(cmd="decide")
async def decide_handler(bot: BOT, message: Message):
    """
    CMD: DECIDE
    INFO: Helps you make a decision by answering your question.
    USAGE:
        .decide [question]
    """
    question = message.input
    
    if not question:
        await message.reply(
            "**What should I decide on?**\n"
            "Usage: `.decide [your question]`",
            del_in=MEDIUM_TIMEOUT
        )
        return

    decision = random.choice(DECIDE_RESPONSES)
    
    final_text = (
        f"**Question:** `{question}`\n\n"
        f"**My decision is:**\n» __{decision}__"
    )

    await message.reply(final_text)
