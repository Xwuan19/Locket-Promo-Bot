import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Update
from app.config import (
    BOT_TOKEN,
    ADMIN_PASSWORD,
    ADMIN_ID,
    PROMO_REFERRALS_NEEDED
)
from app.bot import create_bot_app
from app.services.promo_engine import run_promo_boost
from app.services.revenuecat_verifier import check_revenuecat_status
from app.database import get_system_stats, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Locket Gold Promo Web Portal & API")
bot_app = create_bot_app()

@app.on_event("startup")
async def on_startup():
    init_db()
    await bot_app.initialize()
    logger.info("FastAPI and Bot initialized.")

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.shutdown()

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Locket Gold Promo Serverless Bot</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-white flex items-center justify-center min-h-screen">
        <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl max-w-md w-full text-center shadow-2xl">
            <div class="text-5xl mb-4">👑</div>
            <h1 class="text-2xl font-bold text-amber-400 mb-2">Locket Gold Promo Bot</h1>
            <p class="text-slate-400 text-sm mb-6">Hệ thống kích hoạt Locket Gold Chế độ 2 (100% No-DNS) hoạt động 24/7 trên Vercel Serverless.</p>
            <div class="space-y-3">
                <a href="/admin" class="block w-full py-3 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-xl transition">Mở Web Admin Portal</a>
                <a href="/set_webhook" class="block w-full py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl transition">⚡ Kích Hoạt Telegram Webhook</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/set_webhook")
async def set_webhook(request: Request):
    host = request.headers.get("host")
    if not host:
        return {"success": False, "error": "Missing host header"}
    webhook_url = f"https://{host}/api/webhook"
    try:
        await bot_app.bot.set_webhook(url=webhook_url)
        return {"success": True, "webhook_url": webhook_url, "message": "Webhook registered successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    try:
        req_json = await request.json()
        update = Update.de_json(req_json, bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error("Webhook processing error: %s", e)
        return Response(status_code=200)

@app.get("/admin", response_class=HTMLResponse)
async def admin_portal():
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Portal - Locket Gold Promo (No-DNS)</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-slate-950 text-slate-100 min-h-screen font-sans">
        <div id="login-modal" class="fixed inset-0 bg-slate-950/90 backdrop-blur flex items-center justify-center p-4 z-50">
            <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl max-w-sm w-full text-center shadow-2xl">
                <div class="text-4xl text-amber-400 mb-3"><i class="fa-solid fa-shield-halved"></i></div>
                <h2 class="text-xl font-bold mb-2">Đăng Nhập Quản Trị</h2>
                <p class="text-slate-400 text-xs mb-4">Nhập mật khẩu quản trị ADMIN_PASSWORD</p>
                <input id="admin-pass" type="password" placeholder="Mật khẩu..." class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-sm text-center mb-4 focus:outline-none focus:border-amber-400">
                <button onclick="login()" class="w-full py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-xl text-sm transition">Đăng Nhập</button>
            </div>
        </div>

        <div class="max-w-5xl mx-auto p-4 md:p-8">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-xl">👑</div>
                    <div>
                        <h1 class="text-xl font-bold">Locket Gold Promo Dashboard</h1>
                        <p class="text-xs text-slate-400">Chế độ 2: Referral & Promo Farm (100% No-DNS)</p>
                    </div>
                </div>
                <button onclick="logout()" class="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg text-slate-300">Đăng Xuất</button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div class="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                    <div class="text-xs text-slate-400">Tổng Đơn Kích Hoạt</div>
                    <div id="stat-total" class="text-2xl font-bold text-amber-400 mt-1">--</div>
                </div>
                <div class="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                    <div class="text-xs text-slate-400">Kích Hoạt Thành Công</div>
                    <div id="stat-success" class="text-2xl font-bold text-emerald-400 mt-1">--</div>
                </div>
                <div class="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                    <div class="text-xs text-slate-400">Cơ Chế Bảo Mật</div>
                    <div class="text-2xl font-bold text-cyan-400 mt-1">No-DNS 100%</div>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl mb-6 shadow-xl">
                <h3 class="text-base font-bold text-amber-400 mb-2 flex items-center gap-2">
                    <i class="fa-solid fa-bolt"></i> Bơm Locket Gold Promo Trực Tiếp (Live Boost)
                </h3>
                <p class="text-xs text-slate-400 mb-4">Nhập Username hoặc Link kết bạn Locket để tự động kích hoạt 30 ngày Gold No-DNS.</p>
                <div class="flex gap-2 mb-4">
                    <input id="boost-input" type="text" placeholder="Nhập username (ví dụ: xwuan1) hoặc link locket.cam/..." class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-amber-400">
                    <button onclick="executeBoost()" id="boost-btn" class="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-6 py-2.5 rounded-xl text-sm transition">⚡ Bơm Gold</button>
                </div>
                <div id="boost-log" class="hidden bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300"></div>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
                <h3 class="text-base font-bold text-cyan-400 mb-2 flex items-center gap-2">
                    <i class="fa-solid fa-magnifying-glass"></i> Kiểm Tra Trạng Thái RevenueCat (Live Check)
                </h3>
                <div class="flex gap-2 mb-4">
                    <input id="check-input" type="text" placeholder="Nhập username hoặc UID..." class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-400">
                    <button onclick="executeCheck()" class="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold px-6 py-2.5 rounded-xl text-sm transition">Kiểm Tra</button>
                </div>
                <div id="check-log" class="hidden bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300"></div>
            </div>
        </div>

        <script>
            function login() {
                const pass = document.getElementById('admin-pass').value;
                if (!pass) return alert('Vui lòng nhập mật khẩu!');
                sessionStorage.setItem('admin_pass', pass);
                document.getElementById('login-modal').classList.add('hidden');
                loadStats();
            }

            function logout() {
                sessionStorage.removeItem('admin_pass');
                location.reload();
            }

            if (sessionStorage.getItem('admin_pass')) {
                document.getElementById('login-modal').classList.add('hidden');
                loadStats();
            }

            async function loadStats() {
                try {
                    const res = await fetch('/api/admin/stats');
                    const d = await res.json();
                    document.getElementById('stat-total').innerText = d.total_orders || 0;
                    document.getElementById('stat-success').innerText = d.success_orders || 0;
                } catch(e) {}
            }

            async function executeBoost() {
                const input = document.getElementById('boost-input').value.trim();
                if (!input) return alert('Vui lòng nhập username hoặc link!');
                const btn = document.getElementById('boost-btn');
                const log = document.getElementById('boost-log');
                btn.disabled = true;
                btn.innerText = 'Đang xử lý...';
                log.classList.remove('hidden');
                log.innerHTML = '⏳ Bắt đầu tiến trình Promo Boost...\n';

                try {
                    const res = await fetch('/api/admin/boost', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({identifier: input})
                    });
                    const d = await res.json();
                    if (d.success) {
                        log.innerHTML += `\n✅ KÍCH HOẠT THÀNH CÔNG!\n👤 User: ${d.target_username}\n🆔 UID: ${d.target_uid}\n🎁 Gói: ${d.product_identifier}\n⏳ Hạn dùng: ${d.expires_date}\n🛡️ Tình trạng: 🟢 100% No-DNS!`;
                        loadStats();
                    } else {
                        log.innerHTML += `\n❌ THẤT BÀI: ${d.message || 'Lỗi không xác định'}`;
                    }
                } catch(e) {
                    log.innerHTML += `\n❌ Lỗi kết nối: ${e.message}`;
                } finally {
                    btn.disabled = false;
                    btn.innerText = '⚡ Bơm Gold';
                }
            }

            async function executeCheck() {
                const input = document.getElementById('check-input').value.trim();
                if (!input) return alert('Vui lòng nhập username hoặc UID!');
                const log = document.getElementById('check-log');
                log.classList.remove('hidden');
                log.innerHTML = '⏳ Đang tra cứu RevenueCat...\n';

                try {
                    const res = await fetch('/api/admin/check/' + encodeURIComponent(input));
                    const d = await res.json();
                    log.innerHTML = JSON.stringify(d, null, 2);
                } catch(e) {
                    log.innerHTML = '❌ Lỗi: ' + e.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/admin/boost")
async def api_admin_boost(request: Request):
    try:
        body = await request.json()
        identifier = body.get("identifier", "").strip()
        if not identifier:
            return JSONResponse({"success": False, "message": "Thiếu identifier"}, status_code=400)
        res = await run_promo_boost(identifier)
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)

@app.get("/api/admin/check/{identifier}")
async def api_admin_check(identifier: str):
    res = await check_revenuecat_status(identifier)
    return JSONResponse(res)

@app.get("/api/admin/stats")
async def api_admin_stats():
    stats = get_system_stats()
    return JSONResponse(stats)
