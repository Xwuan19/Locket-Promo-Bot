import aiohttp
import asyncio
import logging
import random
import uuid
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseOTPProvider:
    async def get_number(self) -> Dict[str, Any]:
        raise NotImplementedError
    async def get_otp(self, order_id: str) -> Optional[str]:
        raise NotImplementedError
    async def cancel_number(self, order_id: str):
        pass

class SimulatedOTPProvider(BaseOTPProvider):
    """
    Virtual / High-speed simulated provider for zero-cost referral farming
    """
    async def get_number(self) -> Dict[str, Any]:
        country_code = random.choice(["+84", "+1", "+63", "+62", "+44"])
        rand_num = "".join([str(random.randint(0, 9)) for _ in range(9)])
        fake_phone = f"{country_code}{rand_num}"
        order_id = f"sim_{uuid.uuid4().hex[:12]}"
        return {
            "success": True,
            "order_id": order_id,
            "phone_number": fake_phone,
            "country": country_code
        }

    async def get_otp(self, order_id: str) -> Optional[str]:
        await asyncio.sleep(0.5)
        return f"{random.randint(100000, 999999)}"

class SMSActivateProvider(BaseOTPProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sms-activate.org/stubs/handler_api.php"

    async def get_number(self) -> Dict[str, Any]:
        params = {
            "api_key": self.api_key,
            "action": "getNumber",
            "service": "tg",
            "country": "0"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as resp:
                    text = await resp.text()
                    if "ACCESS_NUMBER" in text:
                        parts = text.split(":")
                        return {"success": True, "order_id": parts[1], "phone_number": parts[2]}
                    return {"success": False, "error": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_otp(self, order_id: str) -> Optional[str]:
        params = {
            "api_key": self.api_key,
            "action": "getStatus",
            "id": order_id
        }
        for _ in range(15):
            await asyncio.sleep(2)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.base_url, params=params) as resp:
                        text = await resp.text()
                        if "STATUS_OK" in text:
                            return text.split(":")[1]
            except Exception:
                pass
        return None

def get_otp_provider(provider_type: str = "simulated", api_key: str = "") -> BaseOTPProvider:
    if provider_type == "smsactivate" and api_key:
        return SMSActivateProvider(api_key)
    return SimulatedOTPProvider()
