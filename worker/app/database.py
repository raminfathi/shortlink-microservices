import redis.asyncio as aioredis  # <-- ۱. نام را به 'aioredis' تغییر دادیم تا تداخل نداشته باشد
from redis.exceptions import ResponseError  # <-- ۲. کلاس خطا را مستقیماً وارد کردیم
from .config import settings, logger


class RedisClient:
    def __init__(self, host: str, port: int, db: int):
        self.host = host
        self.port = port
        self.db = db
        self.client = None

    async def connect(self):
        try:
            # VVV --- ۳. از 'aioredis' استفاده می‌کنیم --- VVV
            self.client = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            # ^^^ ----------------------------------- ^^^
            await self.client.ping()
            logger.info(f"Worker successfully connected to Redis at {self.host}")
        except Exception as e:
            logger.error(f"--- WORKER FAILED TO CONNECT TO REDIS: {e} ---")
            self.client = None

    async def disconnect(self):
        if self.client:
            await self.client.close()
            logger.info("Worker Redis connection closed.")

    async def get_client(self):
        if self.client is None:
            await self.connect()

        if self.client is None:
            raise Exception("Worker could not connect to Redis")
        return self.client

    async def create_consumer_group(self, stream_name: str, group_name: str):
        """گروه مصرف‌کننده را در صورت عدم وجود ایجاد می‌کند (XGROUP CREATE)."""
        try:
            await self.client.xgroup_create(stream_name, group_name, id='$', mkstream=True)
            logger.info(f"Consumer group '{group_name}' created for stream '{stream_name}'.")
        # VVV --- ۴. از 'ResponseError' به تنهایی استفاده می‌کنیم --- VVV
        except ResponseError as e:
            # ^^^ --------------------------------------------- ^^^
            if "Consumer Group name already exists" in str(e):
                logger.info(f"Consumer group '{group_name}' already exists.")
            else:
                logger.error(f"Error creating consumer group: {e}")
                raise

    async def read_stream_group(self, stream_name: str, group_name: str, consumer_name: str):
        """یک پیام از استریم برای این مصرف‌کننده می‌خواند (XREADGROUP)."""
        try:
            response = await self.client.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: '>'},
                count=1,
                block=0
            )

            if response:
                message_id = response[0][1][0][0]
                message_data = response[0][1][0][1]
                return message_id, message_data

            return None, None

        except Exception as e:
            logger.error(f"Error reading from stream group: {e}")
            return None, None

    async def acknowledge_message(self, stream_name: str, group_name: str, message_id: str):
        """پیام پردازش شده را تأیید (Acknowledge) می‌کند (XACK)."""
        try:
            await self.client.xack(stream_name, group_name, message_id)
            logger.info(f"Acknowledged message {message_id} in group {group_name}.")
        except Exception as e:
            logger.error(f"Error acknowledging message {message_id}: {e}")

    async def set_hash_field(self, hash_key: str, field: str, value: str):
        """
        یک فیلد را در یک هش تنظیم می‌کند (HSET).
        """
        try:
            await self.client.hset(hash_key, field, value)
            logger.info(f"Set field '{field}' in hash '{hash_key}'.")
        except Exception as e:
            logger.error(f"Error setting hash field '{field}' for key '{hash_key}': {e}")

    # VVV --- این متد جدید است (فاز ۴.۵) --- VVV
    async def increment_hash_field(self, hash_key: str, field: str, amount: int = 1):
        """
        یک فیلد عددی را در یک هش افزایش می‌دهد (HINCRBY).
        ما از این برای شمارش تعداد کلیک‌ها استفاده می‌کنیم.
        """
        try:
            # HINCRBY hash_key field amount
            new_value = await self.client.hincrby(hash_key, field, amount)
            logger.info(f"Incremented '{field}' in '{hash_key}' to {new_value}.")
            return new_value
        except Exception as e:
            logger.error(f"Error incrementing hash field '{field}' for key '{hash_key}': {e}")
            return None
        

    async def update_leaderboard(self, set_key: str, member: str, amount: int = 1):
        """
        Increments the score of a member in a Sorted Set (ZINCRBY).
        """
        try:
            # ZINCRBY key increment member
            new_score = await self.client.zincrby(set_key, amount, member)
            logger.info(f"Leaderboard '{set_key}': Member '{member}' score is now {new_score}.")
            return new_score
        except Exception as e:
            logger.error(f"Error updating leaderboard '{set_key}': {e}")
            return None

    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """
        Checks if the key has exceeded the limit within the time window.
        Returns True if blocked (limit exceeded), False otherwise.
        """
        client = await self.get_client()
        try:
            # 1. Increase the counter
            # INCR returns the new value
            current_count = await client.incr(key)
            
            # 2. If it's the first request (1), set the expiration time
            if current_count == 1:
                await client.expire(key, window)
            
            # 3. Check if limit exceeded
            if current_count > limit:
                logger.warning(f"Rate limit exceeded for {key}: {current_count}/{limit}")
                return True # Blocked
            
            return False # Allowed
            
        except Exception as e:
            logger.error(f"Error checking rate limit for '{key}': {e}")
            # Fail open: If Redis fails, allow the request to prevent outage
            return False

    # VVV --- Phase 8: New Method for TimeSeries --- VVV
    async def add_timeseries_point(self, key: str, value: float = 1.0, retention_ms: int = 0):
        """
        Adds a data point to a Redis TimeSeries key (TS.ADD).
        If the key doesn't exist, it creates it automatically.

        :param key: The timeseries key (e.g., 'ts:clicks:abc')
        :param value: The value to add (usually 1 for a click event)
        :param retention_ms: How long to keep data in milliseconds (0 = forever)
        """
        try:
            # TS.ADD key timestamp value [RETENTION retentionTime] [ON_DUPLICATE policy]
            # '*' means use the current server timestamp
            await self.client.ts().add(key=key, timestamp='*', value=value, retention_msecs=retention_ms)
            logger.info(f"TimeSeries: Added point to '{key}'.")
        except Exception as e:
            logger.error(f"Error adding to TimeSeries '{key}': {e}")
redis_client = RedisClient(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


# ^^^ ----------------------------------- ^^^

async def get_redis_db():
    return await redis_client.get_client()