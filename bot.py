import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.tl.functions.stories import GetPeerStoriesRequest
from telethon.sessions import StringSession

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

userbot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
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

@bot.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    await event.respond(
        "🆘 Yordam:\n\n"
        "✅ Story havolasini yuboring\n"
        "Misol: https://t.me/username/s/123\n\n"
        "✅ Yoki @username yuboring"
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
