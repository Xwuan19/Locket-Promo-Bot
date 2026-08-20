# 📘 TÀI LIỆU BÀN GIAO DỰ ÁN: LOCKET GOLD PROMO BOT (CHẾ ĐỘ 2 - NO DNS)

> **Mục tiêu cốt lõi:** Kích hoạt gói Locket Gold dạng Promotional 30 Ngày (`rc_promo_Gold_custom`) trực tiếp từ máy chủ RevenueCat, **100% KHÔNG CẦN CÀI PROFILE HAY DNS**.  
> **Nền tảng triển khai:** Vercel Serverless Functions + Telegram Bot 20.x + FastAPI Admin Portal.  
> **Ngày khởi tạo & cập nhật:** **2026-08-20**

---

## 1. 🌟 Tổng quan dự án (Project Overview)

- **Tên dự án:** Locket Gold Promo & Referral Automation Bot (Mode 2: No-DNS)
- **Cơ chế hoạt động:**
  - Thay vì sử dụng chung Token StoreKit 2 Receipt (phương pháp Mode 1 cần DNS), Bot thực hiện **tự động hóa quy trình Referral / Friend Fund** qua Locket API.
  - Khi hoàn thành mốc mời bạn bè (3 - 5 lượt), hệ thống backend của Locket sẽ **cấp gói Gold Khuyến mãi (`rc_promo_Gold_custom`) chính chủ** vào UID của khách trên máy chủ RevenueCat.
  - Khách hàng mở app Locket lên sẽ thấy ngay Gold chính chủ đến 30 ngày, **hoàn toàn không cần cài Profile hay chặn NextDNS**.
- **Chế độ bảo mật kép (Dual Security):**
  - **Telegram Bot (Private Mode):** Chỉ duy nhất Telegram Admin ID (`ADMIN_ID = 8374108763`) mới được quyền kích hoạt.
  - **Web Admin Portal (`/admin`):** Được bảo vệ bằng mật khẩu quản trị (`ADMIN_PASSWORD`).

---

## 2. 🏗️ Kiến trúc hệ thống & Luồng xử lý

```mermaid
flowchart TD
    A[Admin gửi Username / Link kết bạn] --> B[Telegram Bot / Web Admin Portal]
    B --> C{Xác thực Admin}
    C -->|Sai ID/Pass| D[Từ chối & Hiển thị liên hệ @zane_le]
    C -->|Hợp lệ| E[Phân giải Locket UID & Referral Code]
    E --> F[Kiểm tra trạng thái RevenueCat hiện tại]
    F --> G[Chạy vòng lặp tạo lượt mời Referral 1..N]
    G --> H[Gửi broadcast Invite Claim tới Locket Backend]
    H --> I[Xác thực đồng bộ & Cấp Gold trên RevenueCat]
    I --> J[Trả kết quả 30 Ngày No-DNS trong 10-15s]
```

---

## 3. 📁 Cấu trúc thư mục mã nguồn

```text
Locket-Promo-Bot/
│
├── api/
│   └── index.py                # FastAPI Serverless & Webhook Vercel & Web Admin (/admin)
│
├── app/
│   ├── __init__.py
│   ├── config.py               # Cấu hình Admin, Bot Token, Thông số Promo, RevenueCat
│   ├── bot.py                  # Telegram Bot Handlers, Live Progress Bar, Bảo mật Private
│   ├── database.py             # Quản lý SQLite tạm trên Vercel (/tmp) & Log đơn
│   │
│   └── services/
│       ├── __init__.py
│       ├── locket_resolver.py  # Phân giải Username & Link kết bạn sang UID 28 ký tự
│       ├── revenuecat_verifier.py # Live Check gói Gold & Hạn dùng trên RevenueCat API
│       ├── otp_service.py      # Module tích hợp SMS OTP ảo (SMS-Activate, 5sim, Simulated)
│       └── promo_engine.py     # Core Engine tự động hóa Referral Boost No-DNS
│
├── handover.md                 # Tài liệu bàn giao & Hướng dẫn setup A-Z
├── gemini.md                   # File cấu hình ngữ cảnh Gemini AI
├── README.md                   # Hướng dẫn nhanh dự án
├── requirements.txt            # Thư viện Python
├── vercel.json                 # Cấu hình Vercel Serverless
├── main.py                     # Chạy Local Polling (Development)
└── setup_webhook.py            # Script kích hoạt Webhook Telegram
```

---

## 4. 🔑 Biến Môi Trường (Environment Variables)

| Tên biến | Giá trị mẫu | Mục đích | Bắt buộc |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | `your_bot_token_from_botfather` | Token Telegram Bot từ @BotFather | **Có** |
| `ADMIN_ID` | `8374108763` | Telegram ID duy nhất có quyền dùng bot | **Có** |
| `ADMIN_PASSWORD` | `admin123` | Mật khẩu truy cập Web Admin Portal (`/admin`) | **Có** |
| `PROMO_REFERRALS_NEEDED` | `3` | Số lượt mời referral cần gửi cho 1 tài khoản | Không |
| `SMS_PROVIDER` | `simulated` | Nhà cung cấp OTP (`simulated`, `smsactivate`, `5sim`) | Không |
| `SMS_API_KEY` | `""` | API Key thuê SIM nếu bật SMS Provider thật | Không |
| `CONTACT_TELEGRAM` | `zane_le` | Username Telegram liên hệ hiển thị cho người lạ | Không |

---

## 5. 🚀 Hướng Dẫn Setup & Triển Khai Lên Vercel

1. **Đẩy mã nguồn lên GitHub:**
   ```bash
   cd C:\Users\ADMIN\Downloads\Locket-Promo-Bot
   git init
   git add .
   git commit -m "feat: initial release Locket Gold Promo Bot (Mode 2 No-DNS)"
   git branch -M main
   git push https://Xwuan19@github.com/Xwuan19/Locket-Promo-Bot.git main
   ```

2. **Deploy lên Vercel:**
   - Truy cập [vercel.com](https://vercel.com) ➔ Bấm **Add New Project** ➔ Chọn repo `Locket-Promo-Bot`.
   - Thêm các biến môi trường tại mục **Environment Variables** (`BOT_TOKEN`, `ADMIN_ID`, `ADMIN_PASSWORD`).
   - Bấm **Deploy** và chờ 30 giây.

3. **Kích hoạt Webhook:**
   - Mở domain Vercel vừa nhận được: `https://locket-promo-bot-xxx.vercel.app/set_webhook`
   - Nhận thông báo `{"success": true, "message": "Webhook registered successfully"}`.

4. **Sử dụng:**
   - Mở Telegram gửi Username hoặc Link kết bạn vào Bot.
   - Hoặc mở `https://locket-promo-bot-xxx.vercel.app/admin` để kích hoạt trên Web Dashboard.
