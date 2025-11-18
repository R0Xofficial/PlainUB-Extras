import html
import asyncio
import requests
from pyrogram.types import Message

from app import BOT, bot

API_URL = "https://api.frankfurter.app/latest"


@bot.add_cmd(cmd=["cash", "currency"])
async def currency_converter_handler(bot: BOT, message: Message):
    """
    CMD: CASH / CURRENCY
    INFO: Converts an amount from one currency to another using real-time rates.
    USAGE:
        .cash [amount] [FROM_CURRENCY] [TO_CURRENCY]
    EXAMPLE:
        .cash 100 PLN USD
        .cash 50 EUR JPY
    """
    
    if not message.input:
        await message.reply(
            "<b>Usage:</b> <code>.cash [amount] [FROM] [TO]</code>\n"
            "<b>Example:</b> <code>.cash 100 PLN USD</code>",
            del_in=10
        )
        return

    parts = message.input.split()
    if len(parts) != 3:
        await message.reply("<b>Invalid format.</b> Please use: `amount FROM TO`.", del_in=8)
        return

    try:
        amount_str, from_currency, to_currency = parts
        amount = float(amount_str)
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
    except ValueError:
        await message.reply("<b>Invalid amount.</b> Please provide a valid number.", del_in=8)
        return

    progress_msg = await message.reply(
        f"<code>Converting {amount:.2f} {from_currency} to {to_currency}...</code>"
    )

    try:
        def do_request():
            params = {
                "amount": amount,
                "from": from_currency,
                "to": to_currency
            }
            return requests.get(API_URL, params=params, timeout=10)

        response = await asyncio.to_thread(do_request)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' not in data or to_currency not in data['rates']:
            raise ValueError(f"Could not get conversion rate for '{to_currency}'. It may be an invalid currency code.")
        
        converted_amount = data['rates'][to_currency]
        single_rate = converted_amount / amount if amount != 0 else 0

        result_text = (
            f"<b>Conversion Result:</b>\n\n"
            f"<code>{amount:.2f} {from_currency}</code> = <b><code>{converted_amount:.2f} {to_currency}</code></b>\n\n"
            f"<i>Exchange rate: 1 {from_currency} ≈ {single_rate:.4f} {to_currency}</i>"
        )
        
        await progress_msg.edit(result_text)

    except Exception as e:
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(str(e))}</code>", del_in=15)
