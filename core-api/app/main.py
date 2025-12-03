from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  # <-- ۱. این import جدید است
from .database import redis_client
from .routers import links
from .config import settings  # <-- ۲. این import جدید است

# ایجاد اپلیکیشن FastAPI
app = FastAPI(
    title="ShortLink Core API",
    description="سرویس اصلی برای ساخت و ریدایرکت لینک‌های کوتاه",
    version="1.0.0"
)

# --- رویدادهای Startup و Shutdown ---
@app.on_event("startup")
async def startup_app():
    # اتصال به ردیس
    await redis_client.connect()

@app.on_event("shutdown")
async def shutdown_app():
    await redis_client.disconnect()

# --- روت‌ها ---
# اضافه کردن روتر لینک‌ها (مانند /links و /{short_id})
app.include_router(links.router)

# VVV --- ۳. این بخش جدید است --- VVV
# سرویس‌دهی فایل‌های استاتیک
# این به FastAPI می‌گوید که هر درخواستی به '/media' را
# به فایل‌های داخل پوشه 'settings.MEDIA_PATH' (یعنی /app/media) مپ کن.
app.mount("/media", StaticFiles(directory=settings.MEDIA_PATH), name="media")
# ^^^ --- پایان بخش جدید --- ^^^


@app.get("/")
def read_root():
    return {"message": "Core API (v2) is running!"}