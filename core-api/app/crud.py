import redis.asyncio as redis
from nanoid import generate
from .config import settings
# VVV --- ۱. این import ها جدید هستند --- VVV
from .database import redis_client  # <-- کلاینت-رپر را وارد می‌کنیم
from . import schemas


# ^^^ --- پایان بخش جدید --- ^^^

async def create_short_link(db: redis.Redis, long_url: str) -> str:
    """
    لینک کوتاه را می‌سازد، آن را ذخیره می‌کند (String) و
    یک کار (Job) برای سرویس کارگر ارسال می‌کند (Stream).
    """

    # ۱. تولید شناسه و کلید
    short_id = generate(size=6)
    redis_key = f"link:{short_id}"

    # ۲. ذخیره لینک اصلی به عنوان یک String
    await db.set(redis_key, str(long_url))

    # ۳. ارسال پیام به استریم برای سرویس کارگر
    job_data = {
        "short_id": str(short_id),
        "long_url": str(long_url)
    }
    await db.xadd(settings.QR_CODE_JOBS_STREAM, job_data)

    # ۴. برگرداندن شناسه به کاربر
    return short_id


async def get_long_url(db: redis.Redis, short_id: str) -> str | None:
    """
    لینک بلند را بر اساس شناسه کوتاه از ردیس می‌خواند (از نوع String).
    """
    redis_key = f"link:{short_id}"
    return await db.get(redis_key)


# VVV --- ۲. این تابع کاملاً جدید است --- VVV
async def get_link_stats(db: redis.Redis, short_id: str) -> schemas.LinkStats | None:
    """
    آمار کامل یک لینک (شامل QR Code) را با خواندن از String و Hash برمی‌گرداند.
    """

    # ۱. اول، لینک اصلی را از String پیدا می‌کنیم
    # (از تابع موجود get_long_url استفاده می‌کنیم)
    long_url = await get_long_url(db, short_id)

    # اگر لینک اصلی وجود نداشته باشد، آماری هم وجود ندارد
    if not long_url:
        return None

    # ۲. حالا، داده‌های اضافی را از Hash می‌خوانیم
    hash_key = f"{settings.DATA_HASH_KEY_PREFIX}:{short_id}"

    # HGETALL تمام فیلدهای هش را به صورت یک دیکشنری برمی‌گرداند
    # ما از 'redis_client' (کلاینت-رپر) برای دسترسی به متد 'get_hash_all' استفاده می‌کنیم
    hash_data = await redis_client.get_hash_all(hash_key)

    # ۳. پاسخ را می‌سازیم
    qr_code_url = None
    if "qr_code_path" in hash_data:
        # آدرس کامل را می‌سازیم
        qr_code_url = f"{settings.BASE_URL}{hash_data['qr_code_path']}"

    short_link = f"{settings.BASE_URL}/{short_id}"

    return schemas.LinkStats(
        short_link=short_link,
        long_url=long_url,
        qr_code_url=qr_code_url
        # (در فاز بعدی، 'total_clicks' را هم به اینجا اضافه خواهیم کرد)
    )
# ^^^ --- پایان تابع جدید --- ^^^

async def track_link_click(db: redis.Redis, short_id: str):
    """
    یک رویداد 'بازدید' (Click) را به استریم آمار ارسال می‌کند.
    """
    # داده‌ای که می‌خواهیم به worker بفرستیم
    event_data = {
        "short_id": str(short_id)
        # در آینده می‌توانیم IP یا User-Agent را هم اینجا اضافه کنیم
    }

    # ارسال به استریم 'analytics_jobs'
    await db.xadd(settings.ANALYTICS_STREAM_NAME, event_data)

async def get_leaderboard(db: redis.Redis, limit: int = 10):
    """
    Retrieves the top links leaderboard from Redis Sorted Set.
    """
    leaderboard_key = "leaderboard:top_links"
    
    # 1. Get raw data from Redis (List of tuples: [(member, score), ...])
    # We use 'redis_client' wrapper because it has the 'get_top_members' method
    top_items = await redis_client.get_top_members(leaderboard_key, limit)
    
    # 2. Format the result
    result = []
    for member, score in top_items:
        result.append({
            "short_id": member,
            "clicks": int(score),
            "stats_url": f"{settings.BASE_URL}/{member}/stats"
        })
        
    return result