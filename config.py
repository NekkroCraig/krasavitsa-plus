import os


def _int_list(value: str):
    return [int(x.strip()) for x in value.split(",") if x.strip()]


API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

# Необязательно. Если задан (например -1001234567890), бот работает только в этой группе.
# Если не задан — работает в любой группе, где команду написал админ.
CHAT = int(os.getenv("CHAT", "0"))

# Кто может управлять ботом (через запятую). Сам аккаунт-юзербот добавляется автоматически.
ADMINS = _int_list(os.getenv("ADMINS", ""))

# Качество видео: 480 / 720 / 1080. 720 — лучший баланс, на слабом CPU 1080 даёт рассинхрон.
VIDEO_QUALITY = os.getenv("VIDEO_QUALITY", "720")

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

for name, val in (("API_ID", API_ID), ("API_HASH", API_HASH),
                  ("SESSION_STRING", SESSION_STRING)):
    if not val:
        raise SystemExit(f"Не задана переменная окружения {name}")
