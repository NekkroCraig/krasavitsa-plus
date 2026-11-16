import asyncio
import glob
import os
import time
import traceback

# Явно создаём event loop (нужно для Pyrogram на новых версиях Python)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

import config

try:
    from pytgcalls.exceptions import NoActiveGroupCall
except ImportError:  # на случай другой версии библиотеки
    class NoActiveGroupCall(Exception):
        pass

VIDEO_Q = {
    "480": VideoQuality.SD_480p,
    "720": VideoQuality.HD_720p,
    "1080": VideoQuality.FHD_1080p,
}.get(config.VIDEO_QUALITY, VideoQuality.HD_720p)

# STUDIO = 48 кГц стерео, максимум качества звука без какой-либо обработки.
AUDIO_Q = AudioQuality.STUDIO

app = Client(
    "vc_userbot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING,
    in_memory=True,
)
calls = PyTgCalls(app)

admins = set(config.ADMINS)
current_file = None          # путь к файлу, который сейчас играет
current_source = None        # исходный файл (для /seek)


def cleanup_downloads(keep=None):
    for f in glob.glob(os.path.join(config.DOWNLOAD_DIR, "*")):
        if f != keep:
            try:
                os.remove(f)
            except OSError:
                pass


def get_media(msg: Message):
    if not msg:
        return None
    if msg.video:
        return msg.video
    if msg.animation:
        return msg.animation
    if msg.document and (msg.document.mime_type or "").startswith("video/"):
        return msg.document
    return None


def make_stream(path: str, start: int = 0) -> MediaStream:
    ffmpeg_params = f"-ss {start}" if start > 0 else None
    return MediaStream(
        path,
        audio_parameters=AUDIO_Q,
        video_parameters=VIDEO_Q,
        ffmpeg_parameters=ffmpeg_params,
    )


@app.on_message(filters.text & (filters.group | filters.channel))
async def handle_commands(client: Client, message: Message):
    global current_file

    text = message.text.strip()
    if not text.startswith(("/", "!", ".")):
        return

    if config.CHAT and message.chat.id != config.CHAT:
        return
    chat_id = message.chat.id

    sender = message.from_user.id if message.from_user else None
    if sender not in admins:
        return

    cmd, *args = text[1:].split()
    cmd = cmd.split("@")[0].lower()

    if cmd == "play":
        media = get_media(message.reply_to_message)
        if not media:
            return await message.reply("❌ Ответь командой /play на видео (или видеофайл).")

        status = await message.reply("⏳ Скачиваю...")
        path = os.path.join(config.DOWNLOAD_DIR, f"v_{message.id}.mp4")
        last_edit = 0.0

        async def progress(done, total):
            nonlocal last_edit
            if time.time() - last_edit < 4:   # не чаще раза в 4 сек, иначе FloodWait
                return
            last_edit = time.time()
            try:
                await status.edit(f"⏳ Скачиваю: {done * 100 // total}%")
            except Exception:
                pass

        try:
            file_path = await client.download_media(media, file_name=path, progress=progress)
            await status.edit("🚀 Запускаю трансляцию...")
            await calls.play(chat_id, make_stream(file_path))
            cleanup_downloads(keep=file_path)
            global current_source
            current_file = current_source = file_path
            await status.edit(f"✅ Играет ({config.VIDEO_QUALITY}p, 48kHz stereo)")
        except NoActiveGroupCall:
            await status.edit("❌ В чате не запущен голосовой чат. Запусти его и повтори /play.")
        except Exception:
            err = traceback.format_exc()
            print(f"[ERROR] {err}")
            await status.edit(f"🔴 Ошибка: {err[-300:]}")

    elif cmd == "stop":
        try:
            await calls.leave_call(chat_id)
        except Exception as e:
            print(f"[stop] {e}")
        cleanup_downloads()
        current_file = None
        await message.reply("⏹ Остановлено.")

    elif cmd == "pause":
        try:
            await calls.pause(chat_id)
            await message.reply("⏸ Пауза.")
        except Exception as e:
            await message.reply(f"🔴 {e}")

    elif cmd == "resume":
        try:
            await calls.resume(chat_id)
            await message.reply("▶️ Продолжаю.")
        except Exception as e:
            await message.reply(f"🔴 {e}")

    elif cmd == "seek":
        # /seek +30, /seek -10 или /seek 120 (абсолютная позиция в секундах)
        if not args or not current_source:
            return await message.reply("Использование: /seek +30 | -10 | 120 (во время воспроизведения)")
        try:
            arg = args[0]
            if arg[0] in "+-":
                pos = int(await calls.time(chat_id)) + int(arg)
            else:
                pos = int(arg)
            pos = max(pos, 0)
            await calls.play(chat_id, make_stream(current_source, start=pos))
            await message.reply(f"⏩ Перемотка на {pos} сек.")
        except Exception as e:
            await message.reply(f"🔴 {e}")

    elif cmd == "ping":
        await message.reply("pong 🏓")


async def main():
    print("--- ЗАПУСК ---")
    await app.start()
    me = await app.get_me()
    admins.add(me.id)
    await calls.start()

    print(f"✅ Запущено как {me.first_name}. Админы: {admins}")
    if config.CHAT:
        try:
            chat = await app.get_chat(config.CHAT)
            print(f"✅ Вижу чат: {chat.title}")
        except Exception as e:
            print(f"⚠️ Нет доступа к чату: {e}")

    await idle()
    await app.stop()


if __name__ == "__main__":
    loop.run_until_complete(main())
