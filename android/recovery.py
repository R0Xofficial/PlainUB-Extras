import html
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions

from app import BOT, bot
from app.modules.settings import MEDIUM_TIMEOUT

@bot.add_cmd(cmd=["orangefox", "of"])
async def orangefox_link_handler(bot: BOT, message: Message):
    """
    CMD: ORANGEFOX / OF
    INFO: Provides a direct link to the official OrangeFox download page.
    USAGE:
        .orangefox [codename]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.orangefox [codename]</code>", del_in=MEDIUM_TIMEOUT)
        return

    codename = message.input.lower()
    recovery_name = "OrangeFox Recovery"
    final_url = f"https://orangefox.download/device/{codename}"
    
    response_text = (
        f"📱 <b>{recovery_name} downloads for <code>{html.escape(codename)}</code></b>\n\n"
        "Click the button below to go to the official download page."
    )
    
    buttons = [[InlineKeyboardButton(f"Go to {recovery_name} website", url=final_url)]]
    
    await message.reply(
        response_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@bot.add_cmd(cmd="twrp")
async def twrp_link_handler(bot: BOT, message: Message):
    """
    CMD: TWRP
    INFO: Provides a direct link to the official TWRP download page.
    USAGE:
        .twrp [codename]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.twrp [codename]</code>", del_in=MEDIUM_TIMEOUT)
        return

    codename = message.input.lower()
    recovery_name = "TWRP"
    final_url = f"https://twrp.me/{codename}"
    
    response_text = (
        f"📱 <b>{recovery_name} downloads for <code>{html.escape(codename)}</code></b>\n\n"
        "Click the button below to go to the official download page."
    )
    
    buttons = [[InlineKeyboardButton(f"Go to {recovery_name} website", url=final_url)]]
    
    await message.reply(
        response_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@bot.add_cmd(cmd=["pitchblack", "pb", "pbrp"])
async def pitchblack_link_handler(bot: BOT, message: Message):
    """
    CMD: PITCHBLACK / PB / PBRP
    INFO: Provides a direct link to the official PitchBlack Recovery Project download page.
    USAGE:
        .pitchblack [codename]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.pitchblack [codename]</code>", del_in=MEDIUM_TIMEOUT)
        return

    codename = message.input.lower()
    recovery_name = "PitchBlack Recovery"
    final_url = f"https://pitchblackrecovery.com/device/{codename}/"
    
    response_text = (
        f"📱 <b>{recovery_name} downloads for <code>{html.escape(codename)}</code></b>\n\n"
        "Click the button below to go to the official download page."
    )
    
    buttons = [[InlineKeyboardButton(f"Go to {recovery_name} website", url=final_url)]]
    
    await message.reply(
        response_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
