import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = None
if BOT_TOKEN:
    bot = Bot(token=BOT_TOKEN)

def send_telegram_message(message: str):
    async def _send():
        if bot and CHAT_ID:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_send())
        else:
            loop.run_until_complete(_send())
    except RuntimeError:
        asyncio.run(_send())