import aiohttp
import asyncio
import logging
import uuid
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone, timedelta
from app.config import (
    TOKEN_SETS,
    PROMO_REFERRALS_NEEDED,
    PROMO_COOLDOWN_SECONDS,
    REVENUECAT_AUTH_BEARER
)
from app.services.locket_resolver import resolve_locket_target
from app.services.revenuecat_verifier import check_revenuecat_status
from app.database import record_promo_order

logger = logging.getLogger(__name__)

async def inject_revenuecat_gold(uid: str) -> Dict[str, Any]:
    """
    Nạp gói StoreKit 2 Gold trực tiếp tới máy chủ RevenueCat cho UID 28 ký tự
    """
    for token_set in TOKEN_SETS:
        fetch_token = token_set.get("fetch_token")
        app_transaction = token_set.get("app_transaction")
        is_sandbox = token_set.get("is_sandbox", False)
        device_id = token_set.get("device_id", "39A73C25-1E05-4350-ADA7-5CD3FE1079E8")
        user_agent = token_set.get("user_agent", "Locket/3 CFNetwork/3860.300.31 Darwin/25.2.0")

        payload = {
            "app_user_id": uid,
            "fetch_token": fetch_token,
            "app_transaction": app_transaction,
            "is_restore": False,
            "observer_mode": False,
            "initiation_source": "purchase"
        }

        headers = {
            "Host": "api.revenuecat.com",
            "Authorization": REVENUECAT_AUTH_BEARER,
            "Content-Type": "application/json",
            "X-StoreKit-Version": "2",
            "X-StoreKit2-Enabled": "true",
            "X-Is-Sandbox": "true" if is_sandbox else "false",
            "X-Apple-Device-Identifier": device_id,
            "User-Agent": user_agent,
            "Accept": "*/*"
        }

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                async with session.post("https://api.revenuecat.com/v1/receipts", json=payload, headers=headers) as resp:
                    if resp.status in [200, 201]:
                        data = await resp.json()
                        sub = data.get("subscriber", {})
                        ent = sub.get("entitlements", {}).get("Gold")
                        if ent:
                            exp_date = ent.get("expires_date")
                            return {
                                "success": True,
                                "product_identifier": ent.get("product_identifier", "locket_gold"),
                                "expires_date": exp_date,
                                "raw_data": data
                            }
        except Exception as e:
            logger.warning("Token injection attempt failed: %s", e)

    return {"success": False, "message": "Không thể nạp quyền qua RevenueCat"}

async def run_promo_boost(
    identifier: str,
    user_id: int = 0,
    referrals_needed: int = PROMO_REFERRALS_NEEDED,
    progress_callback: Optional[Callable[[int, str], Any]] = None
) -> Dict[str, Any]:
    """
    Chạy quy trình kích hoạt Locket Gold mượt mà, phân giải chuẩn UID và kích hoạt 100% thành công
    """
    if progress_callback:
        await progress_callback(20, "🔍 Đang phân giải chính xác UID Locket (28 ký tự)...")

    target = await resolve_locket_target(identifier)
    target_uid = target.get("uid")
    target_user = target.get("username")

    if not target_uid or len(target_uid) != 28:
        if progress_callback:
            await progress_callback(100, f"❌ Không thể tìm thấy UID 28 ký tự cho: {identifier}")
        return {
            "success": False,
            "message": f"Không phân giải được UID Locket cho tài khoản '{identifier}'. Hãy kiểm tra lại username hoặc link kết bạn!"
        }

    if progress_callback:
        await progress_callback(50, f"⚡ Đã nhận diện UID: {target_uid} — Đang kích hoạt Locket Gold...")

    # Nạp quyền Gold
    inject_res = await inject_revenuecat_gold(target_uid)

    if progress_callback:
        await progress_callback(85, "📡 Đang đồng bộ và xác thực quyền Gold trên RevenueCat...")

    # Kiểm tra live status
    status = await check_revenuecat_status(target_uid)

    if status.get("has_gold"):
        exp_date = status.get("expires_date")
        prod_id = status.get("product_identifier")
        days_left = status.get("days_remaining", 30)

        if progress_callback:
            await progress_callback(100, "✅ KÍCH HOẠT LOCKET GOLD THÀNH CÔNG 100%!")

        record_promo_order(user_id, target_user, target_uid, referrals_needed, referrals_needed, "SUCCESS", exp_date)

        return {
            "success": True,
            "target_username": target_user,
            "target_uid": target_uid,
            "product_identifier": prod_id,
            "expires_date": exp_date,
            "days_remaining": days_left,
            "has_gold": True,
            "needs_dns": False
        }
    else:
        if progress_callback:
            await progress_callback(100, "❌ Kích hoạt không thành công")
        return {
            "success": False,
            "target_username": target_user,
            "target_uid": target_uid,
            "message": "Không nhận được phản hồi cấp quyền từ RevenueCat. Vui lòng thử lại!"
        }
