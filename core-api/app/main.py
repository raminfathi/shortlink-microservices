from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# VVV --- 1. Import --- VVV
from prometheus_fastapi_instrumentator import Instrumentator
# ^^^ --- End Import --- ^^^
from .database import redis_client
from .routers import links
from .config import settings

app = FastAPI(
    title="ShortLink Core API",
    description="URL Shortener API with Monitoring",
    version="1.0.0"
)

# VVV --- 2. Activate Monitoring  --- VVV
# This creates the /metrics endpoint
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app)


# ^^^ --- End Monitoring --- ^^^


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