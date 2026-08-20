import os
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    BOT_TOKEN = input("Nhập Telegram BOT_TOKEN: ").strip()

VERCEL_URL = input("Nhập URL Vercel của bạn (ví dụ: https://my-bot.vercel.app): ").strip().rstrip("/")

if not VERCEL_URL.startswith("http"):
    VERCEL_URL = f"https://{VERCEL_URL}"

webhook_url = f"{VERCEL_URL}/api/webhook"
res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}")

print("Kết quả:", res.json())
