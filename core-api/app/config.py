from pydantic_settings import BaseSettings
import logging


class Settings(BaseSettings):
    REDIS_HOST: str = "redis-stack"
    REDIS_PORT: int = 6379  # <--- ۱. پورت ردیس را اضافه می‌کنیم (برای هماهنگی)

    BASE_URL: str = "http://localhost:8000"  # <--- ۲. آدرس پایه را به تنظیمات منتقل می‌کنیم

    # نام استریم
    QR_CODE_JOBS_STREAM: str = "qr_code_jobs"

    # VVV --- ۳. این دو خط جدید هستند --- VVV
    # پیشوند کلید Hash برای داده‌های لینک (QR, آمار)
    DATA_HASH_KEY_PREFIX: str = "data"
    ANALYTICS_STREAM_NAME: str = "analytics_jobs"

    # مسیری که فایل‌های استاتیک (QR Code) در آن قرار دارند
    MEDIA_PATH: str = "/app/media"
    # ^^^ --- پایان بخش جدید --- ^^^


settings = Settings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.config")