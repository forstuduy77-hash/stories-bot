import os
import asyncio
import re
from io import BytesIO
from datetime import datetime, timezone
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaStory, MessageMediaPhoto
from telethon.tl.functions.stories import (
    GetPeerStoriesRequest,
    GetStoriesByIDRequest,
    GetStoriesArchiveRequest,
)
from telethon.sessions import StringSession

STARTUP_TIME = datetime.now(timezone.utc)

ALLOWED_USERS = (
    set(map(int, os.environ.get("ALLOWED_USERS", "").split(",")))
    if os.environ.get("ALLOWED_USERS")
    else set()
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

userbot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot = TelegramClient("bot", API_ID, API_HASH)

# Har foydalanuvchi uchun alohida navbat
queues: dict[int, asyncio.Queue] = {}


async def get_story_by_id(entity, story_id: int):
    try:
        result = await userbot(GetStoriesByIDRequest(peer=entity, id=[story_id]))
        if result.stories:
            return result.stories[0]
    except Exception:
        pass
    try:
        result = await userbot(GetPeerStoriesRequest(peer=entity))
        for story in result.stories.stories:
            if story.id == story_id:
                return story
    except Exception:
        pass
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
                if story.id < story_id:
                    return None
            offset_id = archive.stories[-1].id
    except Exception:
        pass
    return None


async def download_and_send(event, story, msg=None, caption="✅ Story saqlandi!"):
    buf = BytesIO()
    start_time = asyncio.get_event_loop().time()
    done = False

    # Timer — har 5 sekundda xabarni yangilab turadi
    async def show_timer():
        dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while not done:
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            m, s = divmod(elapsed, 60)
            time_str = f"{m:02d}:{s:02d}" if m else f"{s}s"
            if msg:
                try:
                    await msg.edit(f"{dots[i % len(dots)]} Yuklanmoqda... {time_str}")
                except Exception:
                    pass
            i += 1
            await asyncio.sleep(3)

    timer_task = asyncio.create_task(show_timer())
    try:
        await userbot.download_media(story.media, file=buf)
    finally:
        done = True
        timer_task.cancel()

    buf.seek(0)
    if buf.getbuffer().nbytes == 0:
        return False
    ext = ".jpg" if isinstance(story.media, MessageMediaPhoto) else ".mp4"
    buf.name = f"story{ext}"
    if msg:
        await msg.edit("📤 Yuborilmoqda...")
    await bot.send_file(event.chat_id, buf, caption=caption)
    return True


async def process_event(event):
    """Bitta eventni qayta ishlash — forward yoki matn."""

    # ── Forward story ──────────────────────────────────────────────────────
    if (
        event.message
        and event.message.media
        and isinstance(event.message.media, MessageMediaStory)
    ):
        media = event.message.media
        msg = await event.respond("⏳ Yuklanmoqda, iltimos kuting...")
        try:
            entity = await userbot.get_entity(media.peer)
            story = await get_story_by_id(entity, media.id)
            if story is None:
                await msg.edit("❌ Story topilmadi yoki muddati o'tgan!")
            else:
                sent = await download_and_send(event, story, msg=msg)
                if sent:
                    await msg.delete()
                else:
                    await msg.edit("❌ Media yuklab bo'lmadi!")
        except Exception as e:
            await msg.edit(f"❌ Xatolik: {str(e)}")
        return

    # ── Matn xabar ────────────────────────────────────────────────────────
    text = event.text or ""
    if not text:
        return

    story_match = re.search(r"t\.me/([^/]+)/s/(\d+)", text)
    username_match = re.search(r"@([a-zA-Z][a-zA-Z0-9_]{4,})", text)

    if not story_match and not username_match:
        await event.respond(
            "❌ Noto'g'ri format!\n\n"
            "To'g'ri formatlar:\n"
            "• https://t.me/username/s/123\n"
            "• @username"
        )
        return

    msg = await event.respond("⏳ Yuklanmoqda, iltimos kuting...")

    try:
        if story_match:
            username = story_match.group(1)
            story_id = int(story_match.group(2))
            entity = await userbot.get_entity(username)
            story = await get_story_by_id(entity, story_id)
            if story is None:
                await msg.edit("❌ Story topilmadi yoki muddati o'tgan!")
                return
            sent = await download_and_send(event, story, msg=msg)
            if sent:
                await msg.delete()
            else:
                await msg.edit("❌ Media yuklab bo'lmadi!")

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
                    await asyncio.sleep(0.5)
                except Exception:
                    continue
            await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Xatolik: {str(e)}")


async def user_worker(user_id: int, queue: asyncio.Queue):
    """Har foydalanuvchi uchun alohida worker — navbat bilan ishlaydi."""
    while True:
        event = await queue.get()
        try:
            await process_event(event)
        except Exception:
            pass
        queue.task_done()


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


@bot.on(events.NewMessage(pattern="/help"))
async def help_cmd(event):
    await event.respond(
        "🆘 Yordam:\n\n"
        "✅ Bitta story:\n"
        "  https://t.me/username/s/123\n\n"
        "✅ Barcha ochiq storylar:\n"
        "  @username"
    )


@bot.on(events.NewMessage)
async def handle_message(event):
    if event.text and event.text.startswith("/"):
        return
    if event.date and event.date < STARTUP_TIME:
        return
    if ALLOWED_USERS and event.sender_id not in ALLOWED_USERS:
        await event.respond("⛔ Sizga ruxsat yo'q!")
        return

    uid = event.sender_id
    if uid not in queues:
        queues[uid] = asyncio.Queue()
        asyncio.create_task(user_worker(uid, queues[uid]))

    await queues[uid].put(event)


async def main():
    await userbot.connect()
    if not await userbot.is_user_authorized():
        raise RuntimeError("❌ SESSION_STRING noto'g'ri! Yangi SESSION_STRING yarating.")
    print("✅ Userbot ishga tushdi!")
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ Bot ishga tushdi!")
    await asyncio.gather(
        userbot.run_until_disconnected(),
        bot.run_until_disconnected(),
    )


asyncio.run(main())
