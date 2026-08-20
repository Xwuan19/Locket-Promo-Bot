# 🧠 GEMINI AI CONTEXT SPECIFICATION: LOCKET GOLD PROMO BOT (MODE 2 NO-DNS)

---

## 1. Role & Persona
- Bạn là một **Senior Backend & Reverse Engineering Specialist**, am hiểu sâu sắc về kiến trúc Telegram Bot, cơ chế Vercel Serverless Functions, Apple StoreKit 2, RevenueCat API, và các hệ thống Referral / Promotional Entitlement của Locket Camera.

---

## 2. Core Context & Specifications

- **Mục tiêu Chế độ 2 (Mode 2: No-DNS):** Kích hoạt gói Locket Gold dạng Promotional (`rc_promo_Gold_custom`) có thời hạn 30 ngày chính chủ thông qua cơ chế tự động hóa Referral / Friend Fund.
- **Điểm cốt lõi:** Người dùng được cấp quyền Gold trực tiếp trên máy chủ RevenueCat gắn liền với UID của họ, do đó **hoàn toàn KHÔNG CẦN CÀI PROFILE HAY CHẶN DNS**.
- **Môi trường hoạt động:** 
  - **Vercel Serverless (Production):** [https://locket-promo-bot.vercel.app](https://locket-promo-bot.vercel.app)
  - **Telegram Webhook:** `https://locket-promo-bot.vercel.app/api/webhook`
  - **Telegram Bot Active:** [@xwuantest_bot](https://t.me/xwuantest_bot)
  - **Web Admin Dashboard:** `https://locket-promo-bot.vercel.app/admin`
- **Chế độ bảo mật:**
  - **Telegram Bot:** Private Mode — chỉ cho phép duy nhất `ADMIN_ID = 8374108763` sử dụng. Người lạ nhận thông tin liên hệ mua bot: `@zane_le`.
  - **Web Admin Portal (`/admin`):** Bảo vệ bằng `ADMIN_PASSWORD`.

---

## 3. Code Conventions & System Rules

1. **Bất đồng bộ hoàn toàn (Async/Await First):**
   - Mọi I/O (Telegram Bot API, RevenueCat API, Locket Resolver, SMS OTP API) bắt buộc dùng `async/await` và `aiohttp.ClientSession` có timeout từ 4 - 6s.
   - Tuyệt đối không dùng `time.sleep()` trong async handlers làm block event loop.

2. **Safe Env Parsing:**
   - Luôn kiểm tra `.strip()` và `.isdigit()` trước khi parse `int(ADMIN_ID)` để tránh crash `ValueError` trên môi trường Vercel.

3. **Vercel Stateless & File System:**
   - Thư mục gốc trên Vercel là Read-Only. Mọi file SQLite tạm phải lưu tại `/tmp/locket_promo.db`.

4. **Live Progress Feedback:**
   - Khi chạy tiến trình boost promo (mất khoảng 10-15s), Bot phải cập nhật thanh tiến độ Live Progress Bar (0% ➔ 35% ➔ 65% ➔ 90% ➔ 100%) trực tiếp trên tin nhắn Telegram để tạo trải nghiệm người dùng cao cấp.

---

## 4. Mandatory Documentation & Git Protocol

- **BƯỚC 1:** Sau mỗi phiên sửa đổi, nâng cấp hoặc sửa lỗi, bắt buộc cập nhật chi tiết tiến trình vào cả `handover.md` và `gemini.md`.
- **BƯỚC 2:** Chỉ commit mã nguồn sau khi tài liệu đã được cập nhật đầy đủ.
- **BƯỚC 3:** Luôn chỉ định username `Xwuan19` khi thực hiện Git Push:
  ```bash
  git push https://Xwuan19@github.com/Xwuan19/Locket-Promo-Bot.git main
  ```
