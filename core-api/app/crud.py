import redis.asyncio as redis
from nanoid import generate
import json  # <-- 1. Import json for serialization
from .config import settings
from .database import redis_client  # We need our custom wrapper
from . import schemas


async def create_short_link(db: redis.Redis, long_url: str) -> str:
    """
    Creates a short link, saves it (String), and sends a job to worker (Stream).
    """
    # 1. Generate ID
    short_id = generate(size=6)
    redis_key = f"link:{short_id}"

    # 2. Save String
    await db.set(redis_key, str(long_url))

    # 3. Send to Worker
    job_data = {
        "short_id": str(short_id),
        "long_url": str(long_url)
    }
    await db.xadd(settings.QR_CODE_JOBS_STREAM, job_data)

    # 4. Return ID
    return short_id


async def get_long_url(db: redis.Redis, short_id: str) -> str | None:
    """
    Gets the long URL from Redis String.
    Uses Bloom Filter to avoid unnecessary DB lookups (Cache Penetration).
    """
    # 1. Check Bloom Filter first
    bf_key = "bf:short_links"

    # We use our wrapper 'redis_client' to call the custom method
    exists_in_filter = await redis_client.check_bloom_filter(bf_key, short_id)

    # If Bloom Filter says it DEFINITELY does not exist, return None immediately.
    if not exists_in_filter:
        return None

    # 2. If it MIGHT exist, proceed to check the actual database (String)
    redis_key = f"link:{short_id}"
    return await db.get(redis_key)


# VVV --- Updated Function with Caching --- VVV
async def get_link_stats(db: redis.Redis, short_id: str) -> schemas.LinkStats | None:
    """
    Gets full stats with Caching (Look-aside pattern).
    1. Try Cache -> 2. If Miss, Get from DB -> 3. Set Cache -> 4. Return
    """

    # 1. Try Cache
    cache_key = f"cache:stats:{short_id}"
    # Use our wrapper method to get cache
    cached_data = await redis_client.get_cache(cache_key)

    if cached_data:
        # Cache HIT: Parse JSON and return immediately
        data_dict = json.loads(cached_data)
        return schemas.LinkStats(**data_dict)

    # 2. Cache MISS: Get from DB (Existing Logic)
    long_url = await get_long_url(db, short_id)

    if not long_url:
        return None

    hash_key = f"{settings.DATA_HASH_KEY_PREFIX}:{short_id}"
    hash_data = await redis_client.get_hash_all(hash_key)

    qr_code_url = None
    if "qr_code_path" in hash_data:
        qr_code_url = f"{settings.BASE_URL}{hash_data['qr_code_path']}"

    short_link = f"{settings.BASE_URL}/{short_id}"

    uv_key = f"uv:{short_id}"
    unique_clicks = await redis_client.count_hyperloglog(uv_key)
    # ^^^ --- End of new logic --- ^^^

    # Create the object with unique_clicks
    stats_obj = schemas.LinkStats(
        short_link=short_link,
        long_url=long_url,
        qr_code_url=qr_code_url,
        unique_clicks=unique_clicks # <--- Pass the count here
    )

    # 3. Set Cache (TTL: 30 seconds)
    # Serialize the Pydantic model to JSON string
    # We use model_dump() (Pydantic v2) or dict() and then dumps
    await redis_client.set_cache(
        cache_key,
        json.dumps(stats_obj.model_dump(mode='json')),
        ttl=30
    )
    return stats_obj


# ^^^ --- End Updated Function --- ^^^

async def track_link_click(db: redis.Redis, short_id: str):
    """
    Sends a 'click' event to the analytics stream.
    """
    event_data = {
        "short_id": str(short_id)
    }

    await db.xadd(settings.ANALYTICS_STREAM_NAME, event_data)


async def get_leaderboard(db: redis.Redis, limit: int = 10):
    """
    Retrieves the top links leaderboard from Redis Sorted Set.
    """
    leaderboard_key = "leaderboard:top_links"

    top_items = await redis_client.get_top_members(leaderboard_key, limit)

    result = []
    for member, score in top_items:
        result.append({
            "short_id": member,
            "clicks": int(score),
            "stats_url": f"{settings.BASE_URL}/{member}/stats"
        })

    return result


async def get_link_clicks_history(db: redis.Redis, short_id: str):
    """
    Retrieves the click history from Redis TimeSeries.
    """
    # Key format: ts:clicks:{short_id}
    ts_key = f"ts:clicks:{short_id}"

    # Get raw data points [(timestamp, value), ...]
    # We use '-' and '+' to get ALL available history
    raw_data = await redis_client.get_timeseries_range(ts_key, "-", "+")

    # Format for API response
    history = []
    for timestamp, value in raw_data:
        history.append({
            "timestamp": timestamp,  # Unix timestamp in milliseconds
            "count": int(value)
        })

    return history


async def track_link_click(db: redis.Redis, short_id: str, ip: str):
    """
    Sends a 'click' event to the analytics stream, including the user's IP.
    """
    event_data = {
        "short_id": str(short_id),
        "ip": str(ip)  # <-- New Field: Client IP Address
    }

    # Send the event to the Redis Stream defined in settings
    await db.xadd(settings.ANALYTICS_STREAM_NAME, event_data)