import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import requests

BOT_TOKEN = "8830712538:AAGUAH5oRa_YuJV3u5ATxwc__CfVKltUMAg"
API_ID = "14411446"
API_HASH = "bc1b431494ed640470603fc46b5531f5"

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "👋 Salom! Men Telegram Stories Saver botiman!\n\n"
        "📖 Foydalanish:\n"
        "1. Menga stories havolasini yuboring\n"
        "2. Men uni yuklab beraman\n\n"
        "⚡ Bot 24/7 ishlaydi!"
    )

@bot.on(events.NewMessage(pattern='/help'))
async def help(event):
    await event.respond(
        "🆘 Yordam:\n\n"
        "✅ Telegram stories havolasini yuboring\n"
        "✅ Men rasmni yoki videoni yuklab beraman\n\n"
        "❓ Muammo bo'lsa: @sizning_username ga yozing"
    )

@bot.on(events.NewMessage)
async def handle_message(event):
    if event.text and event.text.startswith('/'):
        return
    
    await event.respond("⏳ Yuklanmoqda...")
    
    try:
        if event.media:
            if isinstance(event.media, MessageMediaPhoto):
                file = await bot.download_media(event.media)
                await event.respond(file=file)
                os.remove(file)
            elif isinstance(event.media, MessageMediaDocument):
                file = await bot.download_media(event.media)
                await event.respond(file=file)
                os.remove(file)
        else:
            await event.respond(
                "❌ Stories havolasini yuboring yoki "
                "stories ni forward qiling!"
            )
    except Exception as e:
        await event.respond(f"❌ Xatolik: {str(e)}")

print("✅ Bot ishga tushdi!")
bot.run_until_disconnected()
