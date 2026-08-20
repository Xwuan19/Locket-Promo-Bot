import os

# Telegram Bot Credentials
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

admin_id_raw = os.environ.get("ADMIN_ID", "8374108763").strip()
ADMIN_ID = int(admin_id_raw) if admin_id_raw and admin_id_raw.isdigit() else 8374108763

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123").strip()
CONTACT_TELEGRAM = os.environ.get("CONTACT_TELEGRAM", "zane_le").strip()
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").strip()

# Supabase Dynamic Storage (Pass via Environment Variables)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

# Mode 2 Promo Settings (Referral / Friend Fund)
promo_ref_raw = os.environ.get("PROMO_REFERRALS_NEEDED", "3").strip()
PROMO_REFERRALS_NEEDED = int(promo_ref_raw) if promo_ref_raw and promo_ref_raw.isdigit() else 3

promo_cd_raw = os.environ.get("PROMO_COOLDOWN_SECONDS", "1.2").strip()
try:
    PROMO_COOLDOWN_SECONDS = float(promo_cd_raw)
except ValueError:
    PROMO_COOLDOWN_SECONDS = 1.2

# OTP / SMS Service Provider (simulated, smsactivate, 5sim)
SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "simulated").strip()
SMS_API_KEY = os.environ.get("SMS_API_KEY", "").strip()

# RevenueCat Client Headers & Token
REVENUECAT_AUTH_BEARER = os.environ.get("REVENUECAT_AUTH_BEARER", "Bearer appl_JngFETzdodyLmCREOlwTUtXdQik").strip()
REVENUECAT_API_HOST = "https://api.revenuecat.com"
REVENUECAT_APP_ID = "1600525061"

# UI Visual Constants
E_LOADING = "⏳"
E_SUCCESS = "✅"
E_ERROR = "❌"
E_SPARKLE = "✨"
E_FIRE = "🔥"
E_STAR = "⭐"
E_LOCK = "🔒"
E_ROCKET = "🚀"
E_GIFT = "🎁"
E_SHIELD = "🛡️"
E_REFRESH = "🔄"
E_CHECK = "✔️"
E_LINK = "🔗"
E_USER = "👤"
E_VIP = "👑"
