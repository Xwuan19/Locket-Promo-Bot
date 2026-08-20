import aiohttp
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def extract_uid_from_text(text: str) -> str:
    if not text:
        return None
    
    # 1. users%2F<28_char_uid>%2F
    m1 = re.search(r'users%2F([A-Za-z0-9_-]{28})%2F', text)
    if m1:
        return m1.group(1)

    # 2. users/<28_char_uid>/
    m2 = re.search(r'users/([A-Za-z0-9_-]{28})/', text)
    if m2:
        return m2.group(1)

    # 3. /invites/<28_char_uid>
    m3 = re.search(r'/invites/([A-Za-z0-9_-]{28})', text)
    if m3:
        return m3.group(1)

    # 4. link=...
    lp = re.search(r'link=([^\s"\'>]+)', text)
    if lp:
        try:
            d = lp.group(1).replace('%3A', ':').replace('%2F', '/')
            dm = re.search(r'/invites/([A-Za-z0-9_-]{28})', d) or re.search(r'users/([A-Za-z0-9_-]{28})', d)
            if dm:
                return dm.group(1)
        except Exception:
            pass

    return None

async def resolve_locket_target(identifier: str) -> Dict[str, Any]:
    """
    Phân giải chuẩn xác Username hoặc Link locket.cam sang Locket UID 28 ký tự
    """
    clean_id = identifier.strip()
    
    # Nếu đã là UID 28 ký tự hợp lệ
    clean_username = clean_id.replace("@", "").strip()
    if len(clean_username) == 28 and re.match(r'^[a-zA-Z0-9_-]{28}$', clean_username):
        return {
            "success": True,
            "uid": clean_username,
            "username": clean_username,
            "display_name": clean_username,
            "referral_code": clean_username[:8]
        }

    # Bóc tách link
    url = clean_id
    if not url.startswith("http"):
        url = f"https://locket.cam/{clean_username}"

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
        "Accept": "text/html"
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(url, headers=headers, allow_redirects=True) as resp:
                html = await resp.text()
                redirect_url = str(resp.url)
                
                uid = extract_uid_from_text(redirect_url) or extract_uid_from_text(html)
                if uid:
                    return {
                        "success": True,
                        "uid": uid,
                        "username": clean_username,
                        "display_name": clean_username,
                        "referral_code": clean_username
                    }
    except Exception as e:
        logger.error("Error resolving locket target: %s", e)

    return {
        "success": False,
        "uid": clean_username,
        "username": clean_username,
        "display_name": clean_username,
        "referral_code": clean_username
    }
