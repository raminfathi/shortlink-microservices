import redis.asyncio as aioredis
from redis.exceptions import ResponseError
from .config import settings, logger


class RedisClient:
    def __init__(self, host: str, port: int, db: int):
        self.host = host
        self.port = port
        self.db = db
        self.client = None

    async def connect(self):
        """در زمان استارت‌آپ، به ردیس متصل می‌شود."""
        try:
            self.client = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True  # <-- مهم: پاسخ‌ها را به string تبدیل می‌کند
            )
            await self.client.ping()
            logger.info(f"Core-API successfully connected to Redis at {self.host}")
        except Exception as e:
            logger.error(f"--- CORE-API FAILED TO CONNECT TO REDIS: {e} ---")
            self.client = None

    async def disconnect(self):
        """در زمان شات‌دان، اتصال را می‌بندد."""
        if self.client:
            await self.client.close()
            logger.info("Core-API Redis connection closed.")

    async def get_client(self):
        """کلاینت خام ردیس را برمی‌گرداند."""
        if self.client is None:
            await self.connect()

        if self.client is None:
            raise Exception("Core-API could not connect to Redis")
        return self.client

    # VVV --- این متد جدید این بخش است --- VVV
    async def get_hash_all(self, hash_key: str) -> dict:
        """
        تمام فیلدها و مقادیر یک هش را می‌خواند (HGETALL).
        ما از این برای خواندن آدرس QR Code و آمار بازدید استفاده خواهیم کرد.
        """
        # اطمینان از اتصال (اگرچه 'get_redis_db' این کار را می‌کند)
        client = await self.get_client()
        try:
            # HGETALL hash_key
            result = await client.hgetall(hash_key)
            logger.info(f"Read hash '{hash_key}'.")
            return result  # hgetall در کتابخانه redis-py به طور خودکار dict برمی‌گرداند
        except Exception as e:
            logger.error(f"Error reading hash '{hash_key}': {e}")
            return {}
    # ^^^ --- پایان متد جدید --- ^^^


# --- بخش‌های حیاتی ---

# ۱. ساختن یک نمونه از کلاینت برای استفاده در main.py
redis_client = RedisClient(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


# ۲. ساختن Dependency Injector برای استفاده در روترها
async def get_redis_db():
    """
    وابستگی (Dependency) برای FastAPI که کلاینت خام ردیس را برمی‌گرداند.
    """
    return await redis_client.get_client()