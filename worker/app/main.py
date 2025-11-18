import asyncio  # <-- ۱. این import جدید است
from fastapi import FastAPI
from .database import redis_client
from .config import logger  # <-- ۲. این import جدید است (برای لاگ‌نویسی)
from .listener import listen_for_jobs  # <-- ۳. تابع شنونده را وارد می‌کنیم

app = FastAPI(
    title="ShortLink Worker",
    description="سرویس کارگر برای پردازش کارهای پس‌زمینه (QR, Analytics)",
    version="1.0.0"
)


# --- رویدادهای Startup و Shutdown ---
@app.on_event("startup")
async def startup_app():
    # اتصال به ردیس
    await redis_client.connect()

    # VVV --- ۴. تغییر اصلی در اینجا --- VVV
    # اجرای شنونده در یک وظیفه پس‌زمینه
    # asyncio.create_task آن را در حلقه رویداد (Event Loop) اجرا می‌کند
    # بدون اینکه منتظر بماند تا تمام شود.
    logger.info("Starting background job listener...")
    asyncio.create_task(listen_for_jobs())
    # ^^^ --- پایان تغییر --- ^^^


@app.on_event("shutdown")
async def shutdown_app():
    await redis_client.disconnect()


# --- روت‌ها ---
@app.get("/")
def read_root():
    # این اندپوینت برای چک کردن سلامت (Health Check) سرویس عالی است
    return {"message": "Worker is running and listening!"}