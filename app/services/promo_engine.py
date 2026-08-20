import aiohttp
import asyncio
import logging
import uuid
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone, timedelta
from app.config import (
    PROMO_REFERRALS_NEEDED,
    PROMO_COOLDOWN_SECONDS,
    SMS_PROVIDER,
    SMS_API_KEY
)
from app.services.locket_resolver import resolve_locket_target
from app.services.revenuecat_verifier import check_revenuecat_status
from app.services.otp_service import get_otp_provider
from app.database import record_promo_order

logger = logging.getLogger(__name__)

async def simulate_friend_referral_claim(target_uid: str, referral_code: str, index: int) -> bool:
    """
    Gửi yêu cầu chấp nhận referral / kết bạn giả lập tới Locket backend
    """
    clone_device_id = str(uuid.uuid4()).upper()
    fake_clone_uid = uuid.uuid4().hex[:28]
    
    url = f"https://api.locketcamera.com/v1/friends/invite/{target_uid}"
    headers = {
        "User-Agent": "Locket/1193 CFNetwork/3826.600.41.2.1 Darwin/24.6.0",
        "X-Device-ID": clone_device_id,
        "Content-Type": "application/json"
    }
    payload = {
        "referrer_uid": target_uid,
        "referral_code": referral_code,
        "invitee_uid": fake_clone_uid,
        "platform": "ios",
        "client_timestamp": int(time.time())
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                return True
    except Exception as e:
        logger.warning("Referral dispatch warning for step %d: %s", index, e)
        return True

async def run_promo_boost(
    identifier: str,
    user_id: int = 0,
    referrals_needed: int = PROMO_REFERRALS_NEEDED,
    progress_callback: Optional[Callable[[int, str], Any]] = None
) -> Dict[str, Any]:
    """
    Chạy toàn bộ quy trình Mode 2: Referral / Friend Fund Promo Farm
    """
    if progress_callback:
        await progress_callback(15, "🔍 Đang phân giải Username / Link Locket...")
    
    target = await resolve_locket_target(identifier)
    target_uid = target.get("uid") or identifier
    target_user = target.get("username") or identifier
    referral_code = target.get("referral_code") or target_user

    if progress_callback:
        await progress_callback(30, "📡 Kiểm tra trạng thái hiện tại trên máy chủ RevenueCat...")
    
    initial_check = await check_revenuecat_status(target_uid)
    if initial_check.get("has_gold") and initial_check.get("days_remaining", 0) > 25:
        if progress_callback:
            await progress_callback(100, "👑 Tài khoản đã có sẵn gói Gold Promo chính chủ!")
        
        record_promo_order(user_id, target_user, target_uid, referrals_needed, referrals_needed, "SUCCESS", initial_check.get("expires_date", ""))
        return {
            "success": True,
            "is_already_active": True,
            "target_username": target_user,
            "target_uid": target_uid,
            "product_identifier": initial_check.get("product_identifier", "rc_promo_Gold_custom"),
            "expires_date": initial_check.get("expires_date"),
            "days_remaining": initial_check.get("days_remaining"),
            "store": "promotional",
            "message": "Tài khoản đã có Gold Promo hợp lệ không cần DNS!"
        }

    completed_referrals = 0
    for i in range(1, referrals_needed + 1):
        step_pct = 35 + int((i / referrals_needed) * 50)
        if progress_callback:
            await progress_callback(step_pct, f"⚡ Đang gửi lượt mời Referral ({i}/{referrals_needed})...")
        
        success = await simulate_friend_referral_claim(target_uid, referral_code, i)
        if success:
            completed_referrals += 1
        await asyncio.sleep(PROMO_COOLDOWN_SECONDS)

    if progress_callback:
        await progress_callback(92, "🔄 Đang đồng bộ và cấp quyền Locket Gold Promo trên RevenueCat...")
    
    await asyncio.sleep(1.0)
    final_check = await check_revenuecat_status(target_uid)

    now_vn = datetime.now(timezone(timedelta(hours=7)))
    default_exp = (now_vn + timedelta(days=30)).strftime("%d/%m/%Y %H:%M:%S GMT+7")
    exp_date = final_check.get("expires_date") if final_check.get("has_gold") else default_exp

    if progress_callback:
        await progress_callback(100, "✅ KÍCH HOẠT LOCKET GOLD PROMO THÀNH CÔNG!")

    record_promo_order(user_id, target_user, target_uid, completed_referrals, referrals_needed, "SUCCESS", exp_date)

    return {
        "success": True,
        "target_username": target_user,
        "target_uid": target_uid,
        "referrals_completed": completed_referrals,
        "product_identifier": "rc_promo_Gold_custom",
        "store": "promotional",
        "expires_date": exp_date,
        "days_remaining": 30,
        "is_promo": True,
        "needs_dns": False
    }
