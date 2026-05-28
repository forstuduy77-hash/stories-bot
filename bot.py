import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.functions.stories import GetPeerStoriesRequest
from telethon.sessions import StringSession

BOT_TOKEN = "8830712538:AAGUAH5oRa_YuJV3u5ATxwc__CfVKltUMAg"
API_ID = 14411446
API_HASH = "bc1b431494ed640470603fc46b5531f5"      # BU YERGA API_HASH QOYING
SESSION_STRING = "1ApWapzMBu4lbz02RDCc44XPrmw0HvJYWi9afjpDh58wKBzzR1w2lYwsVqpisUu7seg2RBVwP-ZtIMT0qpRtuNjYiUvtxOTBh43tnUlwEhSSNpMZ2A1GlGoDivpxppR9FjGpxbjpMSjllULanrJ5YlcRJXL_22xq5-Eqo5n4Y92xThUKQmd7rvPEkMoMPeaPM-hfnZQO1ZFSBUQLCgBSpBLnmx8yeo0KgnC_GxbbrNaQrvp4g5LHmnO1tipO8A_txuvrgtDRVpnYdCz3HELlfARqPqcIXS4fls-D9zHt9pXqP-OX0-8p81yORa8ugTAPDMSTRjYHULdIrJxLxIVomxyuPoiyxN8k="

# Userbot - stories yuklab olish uchun
userbot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# Bot - foydalanuvchiga yuborish uchun
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "👋 Salom! Men Telegram Stories Saver botiman!\n\n"
        "📖 Foydalanish:\n"
        "• Story havolasini yuboring\n"
        "  Misol: https://t.me/username/s/123\n"
        "• Yoki @username yuboring\n"
        "  (barcha ochiq storylar yuklanadi)\n\n"
        "⚡ Bot 24/7 ishlaydi!"
    )

@bot.on(events.NewMessage)
async def handle_message(event):
    if event.text and event.text.startswith('/'):
        return

    text = event.text or ""
    msg = await event.respond("⏳ Yuklanmoqda, iltimos kuting...")

    try:
        story_match = re.search(r't\.me/([^/]+)/s/(\d+)', text)
        username_match = re.search(r'@([a-zA-Z][a-zA-Z0-9_]{4,})', text)

        if story_match:
            username = story_match.group(1)
            story_id = int(story_match.group(2))

            async with userbot:
                entity = await userbot.get_entity(username)
                result = await userbot(GetPeerStoriesRequest(peer=entity))

                found = False
                for story in result.stories.stories:
                    if story.id == story_id:
                        file = await userbot.download_media(story.media, file='downloads/')
                        if file:
                            await bot.send_file(event.chat_id, file, caption="✅ Story saqlandi!")
                            os.remove(file)
                            found = True
                        break

                if not found:
                    await msg.edit("❌ Story topilmadi yoki muddati o'tgan!")
                else:
                    await msg.delete()

        elif username_match:
            username = username_match.group(1)

            async with userbot:
                entity = await userbot.get_entity(username)
                result = await userbot(GetPeerStoriesRequest(peer=entity))
                stories = result.stories.stories

                if not stories:
                    await msg.edit("❌ Bu foydalanuvchining ochiq storylari yo'q!")
                    return

                await msg.edit(f"✅ {len(stories)} ta story topildi, yuborilmoqda...")

                for story in stories:
                    try:
                        file = await userbot.download_media(story.media, file='downloads/')
                        if file:
                            await bot.send_file(event.chat_id, file)
                            os.remove(file)
                            await asyncio.sleep(1)
                    except:
                        continue

                await msg.delete()
        else:
            await msg.edit(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri formatlar:\n"
                "• https://t.me/username/s/123\n"
                "• @username"
            )

    except Exception as e:
        await msg.edit(f"❌ Xatolik: {str(e)}")

os.makedirs('downloads', exist_ok=True)

async def main():
    await userbot.start()
    print("✅ Userbot ishga tushdi!")
    print("✅ Bot ishga tushdi!")
    await bot.run_until_disconnected()

asyncio.run(main())
