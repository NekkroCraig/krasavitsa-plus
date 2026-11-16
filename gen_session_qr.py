"""Вход по QR-коду. Запускать ЛОКАЛЬНО на своём ПК.

pip install telethon "qrcode[pil]"
python gen_session_qr.py

Результат: SESSION_STRING в формате Pyrogram 2.x (для бота).
"""
import asyncio
import base64
import os
import struct

import qrcode
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

QR_FILE = "login_qr.png"


def show_qr(url: str):
    qrcode.make(url).save(QR_FILE)
    try:
        os.startfile(QR_FILE)  # Windows: откроет картинку
    except Exception:
        print(f"Открой файл {os.path.abspath(QR_FILE)}")


async def main():
    api_id = int(input("API_ID: ").strip())
    api_hash = input("API_HASH: ").strip()

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    qr = await client.qr_login()
    print("\nНа телефоне: Telegram -> Настройки -> Устройства -> Подключить устройство")
    print("Наведи камеру на QR-код (картинка откроется сама).")
    show_qr(qr.url)

    while True:
        try:
            await qr.wait(30)
            break
        except asyncio.TimeoutError:
            await qr.recreate()   # токен QR живёт ~30 сек, обновляем
            show_qr(qr.url)
            print("QR обновлён, сканируй новый.")
        except SessionPasswordNeededError:
            pw = input("Пароль двухфакторной защиты: ")
            await client.sign_in(password=pw)
            break

    me = await client.get_me()
    dc_id = client.session.dc_id
    auth_key = client.session.auth_key.key
    await client.disconnect()

    # Формат строки сессии Pyrogram 2.x
    packed = struct.pack(">BI?256sQ?", dc_id, api_id, False, auth_key, me.id, False)
    session = base64.urlsafe_b64encode(packed).decode().rstrip("=")

    print(f"\nВошёл как: {me.first_name} (ID {me.id})")
    print("\n=== SESSION_STRING (никому не показывай!) ===\n")
    print(session)

    try:
        os.remove(QR_FILE)
    except OSError:
        pass


asyncio.run(main())
