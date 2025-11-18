from pydantic_settings import BaseSettings
import os
import logging
from pydantic import Field
import socket


class Settings(BaseSettings):
    """
    تنظیمات سرویس کارگر
    """
    REDIS_HOST: str = "redis-stack"
    REDIS_PORT: int = 6379
    # VVV --- اصلاح ناهماهنگی نام --- VVV
    # نام استریم‌هایی که به آن‌ها گوش خواهیم داد
    # این نام باید با core-api (فرستنده) و listener.py (گیرنده) هماهنگ باشد
    QR_CODE_JOBS_STREAM: str = "qr_code_jobs"  # <--- نام متغیر به حالت قبل برگشت
    MEDIA_PATH: str = "/app/media"
    # این برای فاز بعدی عالی است
    ANALYTICS_STREAM_NAME: str = "analytics_jobs"
    ANALYTICS_CONSUMER_GROUP: str = "analytics_processors"

    # ^^^ --- پایان اصلاح --- ^^^

    QR_CODE_CONSUMER_GROUP: str = "qr_code_processors"
    CONSUMER_NAME: str = Field(default_factory=socket.gethostname)  # این کاملاً درست است


settings = Settings()

logging.basicConfig(level=logging.INFO)
# نام لاگر  را "app.config" می‌گذاریم تا با لاگ‌های قبلی هماهنگ باشد
logger = logging.getLogger("app.config")
