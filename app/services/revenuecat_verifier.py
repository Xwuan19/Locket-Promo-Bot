import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from app.config import REVENUECAT_AUTH_BEARER, REVENUECAT_API_HOST

logger = logging.getLogger(__name__)

def format_rc_date(iso_str: str) -> str:
    if not iso_str:
        return "Không xác định"
    try:
        clean = iso_str.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(clean)
        dt_vn = dt_utc.astimezone(timezone(timedelta(hours=7)))
        return dt_vn.strftime("%d/%m/%Y %H:%M:%S GMT+7")
    except Exception:
        return iso_str

async def check_revenuecat_status(app_user_id: str) -> Dict[str, Any]:
    """
    Kiểm tra live subscriber trên RevenueCat API
    """
    url = f"{REVENUECAT_API_HOST}/v1/subscribers/{app_user_id}"
    headers = {
        "Authorization": REVENUECAT_AUTH_BEARER,
        "X-StoreKit-Version": "2",
        "User-Agent": "Locket/1193 CFNetwork/3826.600.41.2.1 Darwin/24.6.0",
        "Accept": "application/json"
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    subscriber = data.get("subscriber", {})
                    entitlements = subscriber.get("entitlements", {})
                    gold_ent = entitlements.get("Gold")

                    if gold_ent:
                        exp_iso = gold_ent.get("expires_date")
                        prod_id = gold_ent.get("product_identifier", "Gold")
                        purchase_iso = gold_ent.get("purchase_date")
                        
                        days_left = 30
                        if exp_iso:
                            try:
                                dt_exp = datetime.fromisoformat(exp_iso.replace("Z", "+00:00"))
                                now_utc = datetime.now(timezone.utc)
                                days_left = max(0, (dt_exp - now_utc).days)
                            except Exception:
                                pass

                        is_promo = ("promo" in prod_id.lower()) or (subscriber.get("subscriptions", {}).get(prod_id, {}).get("store") == "promotional")

                        return {
                            "has_gold": True,
                            "product_identifier": prod_id,
                            "store": "promotional" if is_promo else "app_store",
                            "is_promo": is_promo,
                            "expires_date": format_rc_date(exp_iso),
                            "purchase_date": format_rc_date(purchase_iso),
                            "raw_expires_date": exp_iso,
                            "days_remaining": days_left,
                            "original_app_user_id": subscriber.get("original_app_user_id", app_user_id)
                        }
                    else:
                        return {
                            "has_gold": False,
                            "message": "Tài khoản hiện chưa có gói Gold",
                            "original_app_user_id": subscriber.get("original_app_user_id", app_user_id)
                        }
                else:
                    return {
                        "has_gold": False,
                        "error_code": resp.status,
                        "message": f"RevenueCat phản hồi mã {resp.status}"
                    }
    except Exception as e:
        logger.error("RevenueCat status error: %s", e)
        return {
            "has_gold": False,
            "error": str(e),
            "message": "Không thể kết nối RevenueCat API"
        }
