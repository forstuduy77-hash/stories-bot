import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.stories import GetPeerStoriesRequest
import re

BOT_TOKEN = "8830712538:AAGUAH5oRa_YuJV3u5ATxwc__CfVKltUMAg"
API_ID = 14411446
API_HASH = "bc1b431494ed640470603fc46b5531f5"

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "👋 Salom! Men Telegram Stories Saver botiman!\n\n"
        "📖 Foydalanish:\n"
        "• Story havolasini yuboring (https://t.me/username/s/123)\n"
        "• Yoki @username yuboring\n\n"
        "⚡ Bot 24/7 ishlaydi!"
    )

@bot.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    await event.respond(
        "🆘 Yordam:\n\n"
        "✅ Story havolasini yuboring\n"
        "Misol: https://t.me/username/s/123\n\n"
        "✅ Yoki faqat @username yuboring\n"
        "Bot barcha ochiq storylarni yuboradi"
    )

@bot.on(events.NewMessage)
async def handle_message(event):
    if event.text and event.text.startswith('/'):
        return

    text = event.text or ""
    
    msg = await event.respond("⏳ Yuklanmoqda, iltimos kuting...")

    try:
        # t.me/username/s/123 formatini tekshirish
        story_match = re.search(r't\.me/([^/]+)/s/(\d+)', text)
        username_match = re.search(r'@?([a-zA-Z][a-zA-Z0-9_]{4,})', text)

        if story_match:
            username = story_match.group(1)
            story_id = int(story_match.group(2))
            
            entity = await bot.get_entity(username)
            result = await bot(GetPeerStoriesRequest(peer=entity))
            
            found = False
            for story in result.stories.stories:
                if story.id == story_id:
                    file = await bot.download_media(story.media, file='downloads/')
                    if file:
                        await bot.send_file(event.chat_id, file, caption=f"✅ Story saqlandi!")
                        os.remove(file)
                        found = True
                    break
            
            if not found:
                await msg.edit("❌ Story topilmadi yoki muddati o'tgan!")

        elif username_match:
            username = username_match.group(1)
            entity = await bot.get_entity(username)
            result = await bot(GetPeerStoriesRequest(peer=entity))
            
            stories = result.stories.stories
            if not stories:
                await msg.edit("❌ Bu foydalanuvchining ochiq storylari yo'q!")
                return

            await msg.edit(f"✅ {len(stories)} ta story topildi, yuborilmoqda...")
            
            for story in stories:
                try:
                    file = await bot.download_media(story.media, file='downloads/')
                    if file:
                        await bot.send_file(event.chat_id, file)
                        os.remove(file)
                        await asyncio.sleep(1)
                except:
                    continue
        else:
            await msg.edit(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri formatlar:\n"
                "• https://t.me/username/s/123\n"
                "• @username"
            )

    except Exception as e:
        await msg.edit(f"❌ Xatolik yuz berdi: {str(e)}")

os.makedirs('downloads', exist_ok=True)
print("✅ Bot ishga tushdi!")
bot.run_until_disconnected()
