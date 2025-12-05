from pydantic_settings import BaseSettings
import logging


class Settings(BaseSettings):
    REDIS_HOST: str = "redis-stack"
    REDIS_PORT: int = 6379
    BASE_URL: str = "http://localhost"

    QR_CODE_JOBS_STREAM: str = "qr_code_jobs"

    DATA_HASH_KEY_PREFIX: str = "data"
    ANALYTICS_STREAM_NAME: str = "analytics_jobs"

    MEDIA_PATH: str = "/app/media"


settings = Settings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.config")