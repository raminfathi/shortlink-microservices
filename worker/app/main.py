import asyncio
from fastapi import FastAPI
from .database import redis_client
from .config import logger
from .listener import listen_for_jobs
from .tracing import setup_tracing  # <-- 1. Import tracing setup

app = FastAPI(
    title="ShortLink Worker",
    description="Worker Service with Tracing",
    version="1.0.0"
)

# --- Observability Setup ---

# 2. Setup Tracing (OpenTelemetry)
# We instrument the worker app so that Redis operations inside it
# are automatically traced and sent to Jaeger.
setup_tracing("worker", app)


# --- Startup & Shutdown ---
@app.on_event("startup")
async def startup_app():
    # Connect to Redis
    await redis_client.connect()

    # Start the background listener loop
    logger.info("Starting background job listener...")
    asyncio.create_task(listen_for_jobs())


@app.on_event("shutdown")
async def shutdown_app():
    await redis_client.disconnect()


# --- Health Check ---
@app.get("/")
def read_root():
    return {"message": "Worker is running and listening!"}