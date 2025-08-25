import html
import asyncio
import requests
from pyrogram.types import Message

from app import BOT, bot

API_URL = "https://wttr.in/"

@bot.add_cmd(cmd=["weather", "wttr"])
async def weather_handler(bot: BOT, message: Message):
    """
    CMD: WEATHER / WTTR
    INFO: Gets the weather for a specified location.
    USAGE:
        .weather [city/location]
    """
    if not message.input:
        await message.reply("<b>Usage:</b> <code>.weather [location]</code>", del_in=8)
        return

    location = message.input.strip()
    progress_msg = await message.reply(f"<code>Fetching weather for {html.escape(location)}...</code>")

    try:
        def do_request():
            params = {"format": "j1"}
            headers = {"User-Agent": "curl/7.81.0"}
            return requests.get(f"{API_URL}{location}", params=params, headers=headers, timeout=10)

        response = await asyncio.to_thread(do_request)
        response.raise_for_status()
        
        data = response.json()

        try:
            current = data['current_condition'][0]
            forecast_today = data['weather'][0]
            forecast_tomorrow = data['weather'][1]
            city = data['nearest_area'][0]['areaName'][0]['value']
            country = data['nearest_area'][0]['country'][0]['value']
            region = data['nearest_area'][0]['region'][0]['value']
            location_name = f"{city}, {region}, {country}"
            chance_of_rain_today = forecast_today['hourly'][4]['chanceofrain']
        except (IndexError, KeyError):
            raise ValueError("Could not parse weather data. Location might be invalid.")

        result_lines = [
            f"<b>Weather for:</b> <code>{html.escape(location_name)}</code>\n",
            f"<b>Now:</b> {current['weatherDesc'][0]['value']} {current['temp_C']}°C (Feels like {current['FeelsLikeC']}°C)",
            f"<b>Wind:</b> {current['windspeedKmph']} km/h from {current['winddir16Point']}",
            f"<b>Humidity:</b> {current['humidity']}%",
            f"<b>Today's Forecast:</b> {forecast_today['maxtempC']}°C / {forecast_today['mintempC']}°C, 🌧️ {chance_of_rain_today}% chance of rain.",
            f"<b>Tomorrow:</b> {forecast_tomorrow['maxtempC']}°C / {forecast_tomorrow['mintempC']}°C"
        ]
        
        await progress_msg.edit("\n".join(result_lines))
        await message.delete()

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            error_msg = f"Location '{location}' not found."
        await progress_msg.edit(f"<b>Error:</b> <code>{html.escape(error_msg)}</code>", del_in=10)
