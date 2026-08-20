import aiohttp
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def resolve_locket_target(identifier: str) -> Dict[str, Any]:
    """
    Phân giải username hoặc link locket.cam/... sang UID 28 ký tự và referral code
    """
    clean_id = identifier.strip()
    
    # 1. Nếu là link locket.cam
    if "locket.cam" in clean_id or "locket.camera" in clean_id or clean_id.startswith("http"):
        match = re.search(r"locket\.cam/([a-zA-Z0-9_\-\.]+)", clean_id)
        if match:
            clean_id = match.group(1).replace("f/", "").replace("f", "")
        else:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
                    async with session.get(clean_id, allow_redirects=True) as resp:
                        final_url = str(resp.url)
                        sub_match = re.search(r"locket\.cam/([a-zA-Z0-9_\-\.]+)", final_url)
                        if sub_match:
                            clean_id = sub_match.group(1).replace("f/", "")
            except Exception as e:
                logger.warning("Failed to follow redirect: %s", e)

    clean_username = clean_id.replace("@", "").strip()

    # Nếu đã là UID 28 ký tự
    if len(clean_username) == 28 and re.match(r"^[a-zA-Z0-9_-]{28}$", clean_username):
        return {
            "success": True,
            "uid": clean_username,
            "username": clean_username,
            "display_name": clean_username,
            "avatar_url": None,
            "referral_code": clean_username[:8]
        }

    api_url = f"https://api.locketcamera.com/v1/users/by_username/{clean_username}"
    headers = {
        "User-Agent": "Locket/1193 CFNetwork/3826.600.41.2.1 Darwin/24.6.0",
        "Accept": "application/json"
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(api_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    uid = data.get("id") or data.get("uid") or data.get("userId") or clean_username
                    return {
                        "success": True,
                        "uid": uid,
                        "username": data.get("username", clean_username),
                        "display_name": data.get("displayName") or data.get("name") or clean_username,
                        "avatar_url": data.get("avatarUrl") or data.get("profilePictureUrl"),
                        "referral_code": clean_username
                    }
                else:
                    return {
                        "success": True,
                        "uid": clean_username if len(clean_username) == 28 else f"user_{clean_username}",
                        "username": clean_username,
                        "display_name": clean_username,
                        "avatar_url": None,
                        "referral_code": clean_username
                    }
    except Exception as e:
        logger.error("Locket resolve error: %s", e)
        return {
            "success": True,
            "uid": clean_username,
            "username": clean_username,
            "display_name": clean_username,
            "avatar_url": None,
            "referral_code": clean_username
        }
