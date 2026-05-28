import os
import asyncio
import re
from io import BytesIO
from datetime import datetime, timezone
from telethon import TelegramClient, events
from telethon.tl.functions.stories import (
    GetPeerStoriesRequest,
    GetStoriesByIDRequest,
    GetStoriesArchiveRequest,
)
from telethon.sessions import StringSession

# Bot ishga tushgan vaqt — bundan oldingi xabarlar e'tiborga olinmaydi
STARTUP_TIME = datetime.now(timezone.utc)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

userbot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot = TelegramClient("bot", API_ID, API_HASH)


async def get_story_by_id(entity, story_id: int):
    """
    Story ID bo'yicha qidiradi:
    1) GetStoriesByIDRequest — eng tez yo'l (jonli + arxiv)
    2) GetPeerStoriesRequest — jonli storylar fallback
    3) GetStoriesArchiveRequest — arxivdan qidirish fallback
    """
    # 1. To'g'ridan-to'g'ri ID bo'yicha so'rash (eng ishonchli)
    try:
        result = await userbot(GetStoriesByIDRequest(peer=entity, id=[story_id]))
        if result.stories:
            return result.stories[0]
    except Exception:
        pass

    # 2. Jonli storylardan qidirish
    try:
        result = await userbot(GetPeerStoriesRequest(peer=entity))
        for story in result.stories.stories:
            if story.id == story_id:
                return story
    except Exception:
        pass

    # 3. Arxivdan qidirish (sahifalab)
    try:
        offset_id = 0
        while True:
            archive = await userbot(
                GetStoriesArchiveRequest(peer=entity, offset_id=offset_id, limit=100)
            )
            if not archive.stories:
                break
            for story in archive.stories:
                if story.id == story_id:
                    return story
                # Arxiv ID kamayib boradi, agar o'tib ketgan bo'lsa to'xtat
                if story.id < story_id:
                    return None
            offset_id = archive.stories[-1].id
    except Exception:
        pass

    return None


async def download_and_send(event, story, caption="✅ Story saqlandi!"):
    """Storydagi mediani xotiradan yuboradi — disk ishlatilmaydi."""
    buf = BytesIO()
    await userbot.download_media(story.media, file=buf)
    buf.seek(0)
    if buf.getbuffer().nbytes == 0:
        return False
    # Fayl nomini media turidan aniqlash
    from telethon.tl.types import MessageMediaPhoto
    ext = ".jpg" if isinstance(story.media, MessageMediaPhoto) else ".mp4"
    buf.name = f"story{ext}"
    await bot.send_file(event.chat_id, buf, caption=caption)
    return True


# ── /start ────────────────────────────────────────────────────────────────────
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond(
        "👋 Salom! Men Telegram Stories Saver botiman!\n\n"
        "📖 Foydalanish:\n"
        "• Story havolasini yuboring\n"
        "  Misol: https://t.me/username/s/123\n"
        "• Yoki @username yuboring (barcha ochiq storylar)\n\n"
        "⚡ Bot 24/7 ishlaydi!"
    )


# ── /help ─────────────────────────────────────────────────────────────────────
@bot.on(events.NewMessage(pattern="/help"))
async def help_cmd(event):
    await event.respond(
        "🆘 Yordam:\n\n"
        "✅ Bitta story:\n"
        "  https://t.me/username/s/123\n\n"
        "✅ Barcha ochiq storylar:\n"
        "  @username"
    )


# ── Forward qilingan story ────────────────────────────────────────────────────
@bot.on(events.NewMessage)
async def handle_forward(event):
    if event.date and event.date < STARTUP_TIME:
        return

    # Forward story aniqlash — turli Telethon versiyalarida turlicha keladi
    story_id = None
    peer = None

    try:
        # Variant 1: event.message.media — MessageStory turi
        from telethon.tl.types import MessageMediaStory
        if event.message and event.message.media and isinstance(event.message.media, MessageMediaStory):
            media = event.message.media
            story_id = media.id
            peer = media.peer
    except Exception:
        pass

    if story_id is None or peer is None:
        return  # Story forward emas — keyingi handlerga o'tadi

    msg = await event.respond("⏳ Yuklanmoqda, iltimos kuting...")
    try:
        entity = await userbot.get_entity(peer)
        story = await get_story_by_id(entity, story_id)

        if story is None:
            await msg.edit("❌ Story topilmadi yoki muddati o'tgan!")
        else:
            sent = await download_and_send(event, story)
            if sent:
                await msg.delete()
            else:
                await msg.edit("❌ Media yuklab bo'lmadi!")
    except Exception as e:
        await msg.edit(f"❌ Xatolik: {str(e)}")


# ── Asosiy handler ────────────────────────────────────────────────────────────
@bot.on(events.NewMessage)
async def handle_message(event):
    if event.text and event.text.startswith("/"):
        return

    # Eski xabarlarni o'tkazib yuborish
    if event.date and event.date < STARTUP_TIME:
        return

    # MessageMediaStory bo'lsa — handle_forward hal qiladi
    try:
        from telethon.tl.types import MessageMediaStory
        if event.message and event.message.media and isinstance(event.message.media, MessageMediaStory):
            return
    except Exception:
        pass

    text = event.text or ""
    if not text:
        return

    msg = await event.respond("⏳ Yuklanmoqda, iltimos kuting...")

    try:
        story_match = re.search(r"t\.me/([^/]+)/s/(\d+)", text)
        username_match = re.search(r"@([a-zA-Z][a-zA-Z0-9_]{4,})", text)

        # ── Bitta story (havola orqali) ────────────────────────────────────
        if story_match:
            username = story_match.group(1)
            story_id = int(story_match.group(2))

            entity = await userbot.get_entity(username)
            story = await get_story_by_id(entity, story_id)

            if story is None:
                await msg.edit("❌ Story topilmadi yoki muddati o'tgan!")
                return

            sent = await download_and_send(event, story)
            if sent:
                await msg.delete()
            else:
                await msg.edit("❌ Media yuklab bo'lmadi!")

        # ── Barcha ochiq storylar (@username) ──────────────────────────────
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
                    await download_and_send(event, story)
                    await asyncio.sleep(1)
                except Exception:
                    continue

            await msg.delete()

        # ── Noto'g'ri format ───────────────────────────────────────────────
        else:
            await msg.edit(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri formatlar:\n"
                "• https://t.me/username/s/123\n"
                "• @username"
            )

    except Exception as e:
        await msg.edit(f"❌ Xatolik: {str(e)}")


# ── Entry point ───────────────────────────────────────────────────────────────
async def main():
    # Userbot — SESSION_STRING bilan ulanadi, telefon so'ramaydi
    await userbot.connect()
    if not await userbot.is_user_authorized():
        raise RuntimeError(
            "❌ SESSION_STRING noto'g'ri yoki muddati o'tgan! "
            "Yangi SESSION_STRING yarating va Railway Variables ga qo'ying."
        )
    print("✅ Userbot ishga tushdi!")

    await bot.start(bot_token=BOT_TOKEN)
    print("✅ Bot ishga tushdi!")
    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected(),
    )


asyncio.run(main())
