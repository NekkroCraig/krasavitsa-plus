"""Запускать ЛОКАЛЬНО на своём компьютере, не на Railway.
pip install pyrogram tgcrypto
python gen_session.py
"""
import asyncio
from pyrogram import Client


async def main():
    api_id = int(input("API_ID: ").strip())
    api_hash = input("API_HASH: ").strip()
    async with Client("gen", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
        print("\n=== SESSION_STRING (никому не показывай!) ===\n")
        print(await app.export_session_string())

asyncio.run(main())
