from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from .database import redis_client
from .routers import links
from .config import settings
from .tracing import setup_tracing  # <-- 1. Import tracing setup

app = FastAPI(
    title="ShortLink Core API",
    description="URL Shortener API with Monitoring and Tracing",
    version="1.0.0"
)

# --- Observability Setup ---

# 2. Setup Tracing (OpenTelemetry)
# This will instrument FastAPI and Redis automatically
# It's important to call this right after creating the 'app'
setup_tracing("core-api", app)

# 3. Setup Metrics (Prometheus)
# We keep this order to ensure /metrics endpoint has high priority
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app)

# --- Startup & Shutdown ---
@app.on_event("startup")
async def startup_app():
    await redis_client.connect()

@app.on_event("shutdown")
async def shutdown_app():
    await redis_client.disconnect()

# --- Routers & Mounts ---
app.include_router(links.router)
app.mount("/media", StaticFiles(directory=settings.MEDIA_PATH), name="media")

@app.get("/")
def read_root():
    return {"message": "Core API (v2) is running!"}