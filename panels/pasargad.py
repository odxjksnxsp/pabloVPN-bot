import aiohttp
import logging
from typing import Tuple, Optional
from .base import BasePanel

logger = logging.getLogger(__name__)

class PasargadPanel(BasePanel):
    async def test_connection(self) -> bool:
        try:
            # دور زدن بررسی SSL برای جلوگیری از خطای Certificate
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(f"{self.url}/api/status", timeout=10) as resp:
                    logger.info(f"🔌 Pasargad status check response: {resp.status}")
                    return resp.status == 200
        except Exception as e:
            logger.error(f"❌ Pasargad status check error: {e}")
            return False

    async def create_user(self, username: str, traffic_gb: float, duration_days: int) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            # آماده‌سازی مقادیر ارسالی با فرمت صحیح عدد صحیح
            payload = {
                "auth_user": self.username,
                "auth_pass": self.password,
                "username": username,
                "traffic": int(traffic_gb),
                "period": int(duration_days)
            }
            
            logger.info(f"🚀 Sending request to Pasargad: {self.url}/api/user/create with payload: {payload}")
            
            # غیرفعال کردن SSL
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(f"{self.url}/api/user/create", json=payload, timeout=15) as resp:
                    status = resp.status
                    text = await resp.text()
                    
                    # چاپ دقیق پاسخ برای مشاهده در لاگ‌های ریلوی
                    logger.info(f"📥 Pasargad Response Status: {status} | Raw Body: {text}")
                    
                    if status in [200, 201]:
                        try:
                            data = await resp.json()
                        except Exception:
                            # اگر پنل هدر JSON نفرستاده بود ولی متن JSON بود
                            import json
                            data = json.loads(text)
                        
                        # پشتیبانی از ساختارهای مختلف خروجی پاسارگاد
                        sub_url = data.get("sub_url") or data.get("subscription_url") or data.get("url") or data.get("sub")
                        config_data = data.get("config") or data.get("config_data") or data.get("link")
                        
                        if sub_url or config_data:
                            logger.info(f"✅ User {username} created successfully on Pasargad!")
                            return True, sub_url, config_data
                        else:
                            logger.warning("⚠️ Pasargad API succeeded but returned empty sub_url or config in JSON.")
                    else:
                        logger.error(f"❌ Pasargad API returned non-success status: {status}")
                        
        except Exception as e:
            logger.error(f"❌ Pasargad create user error: {e}")
            
        return False, None, None

    async def delete_user(self, username: str) -> bool:
        try:
            payload = {
                "auth_user": self.username,
                "auth_pass": self.password,
                "username": username
            }
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(f"{self.url}/api/user/delete", json=payload, timeout=10) as resp:
                    logger.info(f"🗑️ Pasargad Delete user {username} status: {resp.status}")
                    return resp.status in [200, 204]
        except Exception as e:
            logger.error(f"❌ Pasargad delete user error: {e}")
            return False
