import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from app.config import (
    BOT_TOKEN,
    ADMIN_ID,
    CONTACT_TELEGRAM,
    E_LOADING,
    E_SUCCESS,
    E_ERROR,
    E_SPARKLE,
    E_FIRE,
    E_STAR,
    E_LOCK,
    E_ROCKET,
    E_GIFT,
    E_SHIELD,
    E_REFRESH,
    E_VIP
)
from app.services.promo_engine import run_promo_boost
from app.services.revenuecat_verifier import check_revenuecat_status
from app.services.locket_resolver import resolve_locket_target
from app.database import get_system_stats, init_db

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def check_auth_or_reject(update: Update) -> bool:
    user = update.effective_user
    if not user or not is_admin(user.id):
        access_denied_msg = (
            f"🔒 <b>HỆ THỐNG LOCKET GOLD VIP PRIVATE</b>\n\n"
            f"⛔ <i>Rất tiếc! Bot này được cấu hình ở chế độ Private (Chỉ dành riêng cho Admin).</i>\n\n"
            f"💎 <b>Dịch vụ cung cấp:</b>\n"
            f"• 👑 Kích hoạt Locket Gold Promo <b>100% No-DNS</b>\n"
            f"• ⚡ Tự động hóa Referral / Friend Fund qua UID\n"
            f"• 🛠️ Mua Source Code & Setup Bot riêng 24/7 trên Vercel\n\n"
            f"📞 <b>Liên hệ Telegram Admin:</b> @{CONTACT_TELEGRAM}"
        )
        if update.message:
            await update.message.reply_text(access_denied_msg, parse_mode=ParseMode.HTML)
        elif update.callback_query:
            await update.callback_query.answer("⛔ Bạn không có quyền truy cập bot này!", show_alert=True)
        return False
    return True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_or_reject(update):
        return

    keyboard = [
        [InlineKeyboardButton("⚡ Bơm Gold Promo (No-DNS)", callback_data="btn_boost_guide")],
        [
            InlineKeyboardButton("🔍 Kiểm Tra Hạn Dùng", callback_data="btn_check_guide"),
            InlineKeyboardButton("📊 Thống Kê Bot", callback_data="btn_stats")
        ],
        [InlineKeyboardButton("📖 Hướng Dẫn Sử Dụng", callback_data="btn_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👑 <b>LOCKET GOLD PROMO BOT — CHẾ ĐỘ 2 (NO-DNS)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>Chào mừng Admin! Hệ thống tự động hóa Referral / Friend Fund Promo.</i>\n\n"
        f"🎁 <b>Đặc điểm nổi bật:</b>\n"
        f"• 🟢 <b>100% KHÔNG CẦN CÀI DNS HOẶC PROFILE</b>\n"
        f"• 🚀 Cấp gói <code>rc_promo_Gold_custom</code> trực tiếp từ RevenueCat\n"
        f"• ⏱️ Kích hoạt tự động chỉ trong 10 - 15 giây\n\n"
        f"👉 <b>Cách dùng:</b> Hãy gửi trực tiếp <b>Username</b> (ví dụ: <code>xwuan1</code>) hoặc <b>Link kết bạn</b> vào đây!"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_or_reject(update):
        return

    text = update.message.text.strip()
    if text.startswith("/"):
        return

    status_msg = await update.message.reply_text(
        f"{E_LOADING} <b>Khởi tạo tiến trình Promo Boost...</b>\n[░░░░░░░░░░] 0%",
        parse_mode=ParseMode.HTML
    )

    last_text = ""

    async def update_progress(percent: int, message: str):
        nonlocal last_text
        bars = int(percent / 10)
        progress_bar = "█" * bars + "░" * (10 - bars)
        new_text = (
            f"<b>⚡ TIẾN TRÌNH KÍCH HOẠT LOCKET GOLD PROMO</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{message}\n\n"
            f"<b>Tiến độ:</b> [<code>{progress_bar}</code>] {percent}%"
        )
        if new_text != last_text:
            try:
                await status_msg.edit_text(new_text, parse_mode=ParseMode.HTML)
                last_text = new_text
            except Exception:
                pass

    try:
        result = await run_promo_boost(
            identifier=text,
            user_id=update.effective_user.id,
            progress_callback=update_progress
        )

        if result.get("success"):
            target_user = result.get("target_username")
            target_uid = result.get("target_uid")
            exp_date = result.get("expires_date")
            prod_id = result.get("product_identifier", "rc_promo_Gold_custom")

            success_card = (
                f"🎉 <b>KÍCH HOẠT LOCKET GOLD PROMO THÀNH CÔNG!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Tài khoản:</b> <code>{target_user}</code>\n"
                f"🆔 <b>UID:</b> <code>{target_uid}</code>\n"
                f"🎁 <b>Gói cước:</b> <code>{prod_id}</code>\n"
                f"⏳ <b>Hạn dùng:</b> <code>{exp_date}</code> (30 Ngày)\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🛡️ <b>Tình trạng:</b> 🟢 <b>100% KHÔNG CẦN CÀI PROFILE / DNS</b>\n"
                f"✨ <i>Tài khoản đã có Gold chính chủ từ máy chủ RevenueCat!</i>"
            )
            await status_msg.edit_text(success_card, parse_mode=ParseMode.HTML)
        else:
            await status_msg.edit_text(
                f"{E_ERROR} <b>Kích hoạt thất bại:</b> {result.get('message', 'Lỗi không xác định')}",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error("Error handling promo boost: %s", e)
        await status_msg.edit_text(f"{E_ERROR} <b>Đã xảy ra lỗi:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_or_reject(update):
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            f"ℹ️ <b>Cú pháp kiểm tra:</b> <code>/check &lt;username_hoặc_link&gt;</code>",
            parse_mode=ParseMode.HTML
        )
        return

    identifier = args[0].strip()
    wait_msg = await update.message.reply_text(f"{E_LOADING} Đang tra cứu trên máy chủ RevenueCat...", parse_mode=ParseMode.HTML)

    target = await resolve_locket_target(identifier)
    uid = target.get("uid") or identifier

    status = await check_revenuecat_status(uid)

    if status.get("has_gold"):
        res_text = (
            f"👑 <b>THÔNG TIN GÓI LOCKET GOLD TRÊN REVENUECAT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Tài khoản:</b> <code>{target.get('username')}</code>\n"
            f"🆔 <b>UID:</b> <code>{uid}</code>\n"
            f"💎 <b>Gói:</b> <code>{status.get('product_identifier')}</code>\n"
            f"🏷️ <b>Loại:</b> {'🎁 Promo (Chính chủ No-DNS)' if status.get('is_promo') else '💳 StoreKit Receipt'}\n"
            f"⏳ <b>Hết hạn:</b> <code>{status.get('expires_date')}</code>\n"
            f"📅 <b>Còn lại:</b> <b>{status.get('days_remaining')} ngày</b>"
        )
    else:
        res_text = (
            f"ℹ️ <b>KẾT QUẢ TRA CỨU:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Tài khoản:</b> <code>{target.get('username')}</code>\n"
            f"🆔 <b>UID:</b> <code>{uid}</code>\n"
            f"❌ <b>Tình trạng:</b> Tài khoản hiện chưa có quyền Locket Gold active."
        )

    await wait_msg.edit_text(res_text, parse_mode=ParseMode.HTML)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_auth_or_reject(update):
        return

    stats = get_system_stats()
    stats_text = (
        f"📊 <b>THỐNG KÊ LOCKET GOLD PROMO BOT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <b>Tổng lượt kích hoạt:</b> <code>{stats.get('total_orders', 0)}</code>\n"
        f"✅ <b>Thành công:</b> <code>{stats.get('success_orders', 0)}</code>\n"
        f"🟢 <b>Trạng thái hệ thống:</b> Hoạt động 24/7 (Vercel Serverless)"
    )
    if update.message:
        await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.message.edit_text(stats_text, parse_mode=ParseMode.HTML)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "btn_boost_guide":
        await query.message.reply_text(
            "⚡ <b>HƯỚNG DẪN BƠM GOLD PROMO (NO-DNS):</b>\n\n"
            "Chỉ cần gửi thẳng <b>Username Locket</b> (ví dụ: <code>xwuan1</code>) hoặc <b>Link kết bạn</b> vào tin nhắn, bot sẽ tự động xử lý và kích hoạt 30 ngày Gold No-DNS!",
            parse_mode=ParseMode.HTML
        )
    elif data == "btn_check_guide":
        await query.message.reply_text(
            "🔍 <b>HƯỚNG DẪN KIỂM TRA:</b>\n\n"
            "Gõ lệnh: <code>/check &lt;username&gt;</code> để kiểm tra trực tiếp trạng thái Gold và ngày hết hạn trên máy chủ RevenueCat!",
            parse_mode=ParseMode.HTML
        )
    elif data == "btn_stats":
        await stats_command(update, context)
    elif data == "btn_help":
        await start_command(update, context)

def create_bot_app() -> Application:
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    return app
