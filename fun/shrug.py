from pyrogram.types import Message, ReplyParameters

from app import BOT, bot

@bot.add_cmd(cmd="shrug")
async def codeit_handler(bot: BOT, message: Message):
    replied_msg = message.replied

    shrug = r"`¯\_(ツ)_/¯`"

    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=shrug,
            reply_parameters=ReplyParameters(
                message_id=replied_msg.id if replied_msg else message.id
            )
        )

    except Exception as e:
        error_text = f"Error: `{str(e)}`"
        await message.reply(error_text, del_in=8)
