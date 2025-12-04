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
    async def update_leaderboard(self, set_key: str, member: str, amount: int = 1):
        """
        Increments the score of a member in a Sorted Set (ZINCRBY).
        Used for the top links leaderboard.
        """
        try:
            # ZINCRBY key increment member
            new_score = await self.client.zincrby(set_key, amount, member)
            logger.info(f"Leaderboard '{set_key}': Member '{member}' score is now {new_score}.")
            return new_score
        except Exception as e:
            logger.error(f"Error updating leaderboard '{set_key}': {e}")
            return None

    async def get_top_members(self, set_key: str, count: int = 10) -> list:
        """
        Returns the top members of a Sorted Set (ZREVRANGE).
        Includes scores.
        """
        client = await self.get_client()
        try:
            # ZREVRANGE key start stop WITHSCORES
            # 0 to count-1 means top 'count' members
            # withscores=True causes Redis to return tuples: (member, score)
            top_list = await client.zrevrange(set_key, 0, count - 1, withscores=True)
            # Output format: [('link1', 100.0), ('link2', 50.0)]
            return top_list
        except Exception as e:
            logger.error(f"Error reading leaderboard '{set_key}': {e}")
            return []


    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """
        Checks if the key has exceeded the limit within the time window.
        Returns True if blocked (limit exceeded), False otherwise.
        """
        client = await self.get_client()
        try:
            # 1. Increase the counter
            # INCR returns the new value (1, 2, 3, ...)
            current_count = await client.incr(key)

            # 2. If it's the first request (1), set the expiration time for the window
            if current_count == 1:
                await client.expire(key, window)

            # 3. Check if limit exceeded
            if current_count > limit:
                logger.warning(f"Rate limit exceeded for {key}: {current_count}/{limit}")
                return True  # Blocked

            return False  # Allowed

        except Exception as e:
            logger.error(f"Error checking rate limit for '{key}': {e}")
            # Fail open: If Redis fails, allow the request to prevent outage
            return False
    async def get_cache(self, key: str) -> str | None:
        """
        Retrieves a value from cache (GET).
        """
        client = await self.get_client()
        try:
            val = await client.get(key)
            if val:
                logger.info(f"Cache HIT for key: {key}")
            else:
                logger.info(f"Cache MISS for key: {key}")
            return val
        except Exception as e:
            logger.error(f"Error getting cache for {key}: {e}")
            return None

    async def set_cache(self, key: str, value: str, ttl: int):
        """
        Sets a value in cache with expiration (SETEX).
        ttl: Time To Live in seconds.
        """
        client = await self.get_client()
        try:
            # SETEX key seconds value
            await client.setex(key, ttl, value)
            logger.info(f"Cache SET for key: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Error setting cache for {key}: {e}")
    # ^^^ --- End Caching Methods --- ^^^

# ۱. ساختن یک نمونه از کلاینت برای استفاده در main.py
redis_client = RedisClient(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


# ۲. ساختن Dependency Injector برای استفاده در روترها
async def get_redis_db():
    """
    وابستگی (Dependency) برای FastAPI که کلاینت خام ردیس را برمی‌گرداند.
    """
    return await redis_client.get_client()