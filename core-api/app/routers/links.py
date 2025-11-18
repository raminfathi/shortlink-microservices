import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse

# --- اینها بخش‌های حیاتی هستند ---
from .. import schemas, crud
from ..config import settings
from ..database import get_redis_db

# --- تعریف روتر ---
router = APIRouter(
    tags=["Links"]  # دسته‌بندی در داکیومنت Swagger
)


@router.post("/links", response_model=schemas.LinkCreateResponse, status_code=201)
async def create_link_endpoint(
        request: schemas.LinkCreateRequest,
        db: redis.Redis = Depends(get_redis_db)
):
    """
    اندپوینت ساخت لینک کوتاه.
    """
    # ما در اینجا request.long_url را به str تبدیل می‌کنیم
    # تا مطمئن شویم که crud.py یک رشته ساده دریافت می‌کند.
    short_id = await crud.create_short_link(db, str(request.long_url))

    short_link = f"{settings.BASE_URL}/{short_id}"

    return schemas.LinkCreateResponse(
        short_link=short_link,
        long_url=request.long_url
    )


@router.get("/{short_id}")
async def redirect_endpoint(
        short_id: str,
        background_tasks: BackgroundTasks,  # <-- ۲. این پارامتر جدید است
        db: redis.Redis = Depends(get_redis_db)
):
    """
    اندپوینت ریدایرکت.
    """
    long_url = await crud.get_long_url(db, short_id)

    if long_url:
        # ۳. ثبت آمار در پس‌زمینه
        # این خط باعث می‌شود تابع track_link_click *بعد* از ارسال پاسخ به کاربر اجرا شود.
        # این یعنی سرعت ریدایرکت کم نمی‌شود.
        background_tasks.add_task(crud.track_link_click, db, short_id)

        return RedirectResponse(url=long_url, status_code=307)
    else:
        raise HTTPException(status_code=404, detail="Short link not found")
# VVV --- این تابع کاملاً جدید است --- VVV
@router.get("/{short_id}/stats", response_model=schemas.LinkStats)
async def get_link_stats_endpoint(
        short_id: str,
        db: redis.Redis = Depends(get_redis_db)
):
    """
    اندپوینت دریافت آمار (شامل QR Code) برای یک لینک کوتاه.
    """

    # ۱. تابع crud را صدا می‌زنیم تا داده‌ها را از String و Hash بخواند
    stats = await crud.get_link_stats(db, short_id)

    # ۲. اگر لینک وجود نداشته باشد (۴۰۴)
    if not stats:
        raise HTTPException(status_code=404, detail="Link stats not found")

    # ۳. اگر پیدا شد، آبجکت LinkStats را برمی‌گردانیم
    return stats
# ^^^ --- پایان تابع جدید --- ^^^