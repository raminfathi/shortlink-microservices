import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from typing import List # Import List for response model

from .. import schemas, crud
from ..config import settings
from ..database import get_redis_db, redis_client
from ..auth import get_current_user_id


router = APIRouter(
    tags=["Links"]
)


@router.post("/links", response_model=schemas.LinkCreateResponse, status_code=201)
async def create_link_endpoint(
        request: Request,
        link_request: schemas.LinkCreateRequest,
        db: redis.Redis = Depends(get_redis_db),
        user_id: int = Depends(get_current_user_id)
):
    """
    Create a new short link.
    Rate Limited: 5 requests per minute per IP.
    """

    # --- Rate Limiting Logic ---
    # Get client IP
    client_ip = request.client.host
    rate_limit_key = f"rate_limit:{client_ip}"

    # Rule: 5 requests per 60 seconds
    is_blocked = await redis_client.is_rate_limited(rate_limit_key, limit=5, window=60)

    if is_blocked:
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests. You can only create 5 links per minute."
        )
    # --- End Rate Limiting ---

    # Convert HttpUrl to string for Redis compatibility
    short_id = await crud.create_short_link(db, str(link_request.long_url))

    short_link = f"{settings.BASE_URL}/{short_id}"

    return schemas.LinkCreateResponse(
        short_link=short_link,
        long_url=link_request.long_url
    )


@router.get("/{short_id}")
async def redirect_endpoint(
        request: Request,  # <-- 1. Need Request object to get IP
        short_id: str,
        background_tasks: BackgroundTasks,
        db: redis.Redis = Depends(get_redis_db)
):
    """
    Redirect user to the original URL.
    Tracks the click (and IP) in the background.
    """
    long_url = await crud.get_long_url(db, short_id)

    if long_url:
        # Get Client IP
        client_ip = request.client.host

        # 2. Pass IP to the tracking function
        background_tasks.add_task(crud.track_link_click, db, short_id, client_ip)

        return RedirectResponse(url=long_url, status_code=307)
    else:
        raise HTTPException(status_code=404, detail="Short link not found")


@router.get("/{short_id}/stats", response_model=schemas.LinkStats)
async def get_link_stats_endpoint(
        short_id: str,
        db: redis.Redis = Depends(get_redis_db)
):
    """
    Get full statistics for a link (including QR code path).
    """
    stats = await crud.get_link_stats(db, short_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Link stats not found")

    return stats


@router.get("/stats/top", response_model=list)
async def get_top_links_endpoint(
        limit: int = 10,
        db: redis.Redis = Depends(get_redis_db)
):
    """
    Get the top most clicked links from the Redis Sorted Set leaderboard.
    """
    return await crud.get_leaderboard(db, limit)

@router.get("/{short_id}/stats/history", response_model=List[schemas.ClickHistoryItem])
async def get_link_history_endpoint(
    short_id: str,
    db: redis.Redis = Depends(get_redis_db)
):
    """
    Get click history (time-series data) for a specific link.
    """
    # Check if link exists first
    long_url = await crud.get_long_url(db, short_id)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short link not found")

    return await crud.get_link_clicks_history(db, short_id)