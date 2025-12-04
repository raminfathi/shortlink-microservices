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
        """Connects to Redis on startup."""
        try:
            self.client = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            await self.client.ping()
            logger.info(f"Core-API successfully connected to Redis at {self.host}")
        except Exception as e:
            logger.error(f"--- CORE-API FAILED TO CONNECT TO REDIS: {e} ---")
            self.client = None

    async def disconnect(self):
        """Closes connection on shutdown."""
        if self.client:
            await self.client.close()
            logger.info("Core-API Redis connection closed.")

    async def get_client(self):
        """Returns the raw Redis client."""
        if self.client is None:
            await self.connect()

        if self.client is None:
            raise Exception("Core-API could not connect to Redis")
        return self.client

    async def get_hash_all(self, hash_key: str) -> dict:
        client = await self.get_client()
        try:
            result = await client.hgetall(hash_key)
            logger.info(f"Read hash '{hash_key}'.")
            return result
        except Exception as e:
            logger.error(f"Error reading hash '{hash_key}': {e}")
            return {}

    async def get_top_members(self, set_key: str, count: int = 10) -> list:
        client = await self.get_client()
        try:
            top_list = await client.zrevrange(set_key, 0, count - 1, withscores=True)
            return top_list
        except Exception as e:
            logger.error(f"Error reading leaderboard '{set_key}': {e}")
            return []

    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        client = await self.get_client()
        try:
            current_count = await client.incr(key)
            if current_count == 1:
                await client.expire(key, window)

            if current_count > limit:
                logger.warning(f"Rate limit exceeded for {key}: {current_count}/{limit}")
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking rate limit for '{key}': {e}")
            return False

    async def get_cache(self, key: str) -> str | None:
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
        client = await self.get_client()
        try:
            await client.setex(key, ttl, value)
            logger.info(f"Cache SET for key: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Error setting cache for {key}: {e}")

    async def get_timeseries_range(self, key: str, start_timestamp: str = "-", end_timestamp: str = "+") -> list:
        """
        Retrieves data points from a TimeSeries (TS.RANGE).
        start_timestamp: '-' means oldest possible.
        end_timestamp: '+' means newest possible.
        """
        client = await self.get_client()
        try:
            # TS.RANGE key fromTimestamp toTimestamp
            # returns list of tuples: [(timestamp, value), ...]
            data = await client.ts().range(key, from_time=start_timestamp, to_time=end_timestamp)
            return data
        except Exception as e:
            logger.error(f"Error reading TimeSeries '{key}': {e}")
            return []

    async def count_hyperloglog(self, key: str) -> int:
        """
        Returns the approximated number of unique elements in a HyperLogLog (PFCOUNT).
        """
        client = await self.get_client()
        try:
            # PFCOUNT key
            count = await client.pfcount(key)
            return count
        except Exception as e:
            logger.error(f"Error counting HyperLogLog '{key}': {e}")
            return 0
    async def check_bloom_filter(self, key: str, item: str) -> bool:
        """
        Checks if an item exists in a Bloom Filter (BF.EXISTS).
        Returns True if item MIGHT exist.
        Returns False if item DEFINITELY does not exist.
        """
        client = await self.get_client()
        try:
            # BF.EXISTS key item
            exists = await client.bf().exists(key, item)
            # The result is 1 (True) or 0 (False)
            if exists:
                logger.info(f"BloomFilter: '{item}' MIGHT exist in '{key}'.")
                return True
            else:
                logger.info(f"BloomFilter: '{item}' DEFINITELY does not exist in '{key}'.")
                return False
        except Exception as e:
            logger.error(f"Error checking BloomFilter '{key}': {e}")
            # Fail open: If Redis fails, return True to allow DB check (safety fallback)
            return True
redis_client = RedisClient(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


async def get_redis_db():
    return await redis_client.get_client()