import logging
from app.bot import create_bot_app

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    print("🚀 Starting Locket Gold Promo Bot (Mode 2: No-DNS) in Polling Mode...")
    app = create_bot_app()
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
