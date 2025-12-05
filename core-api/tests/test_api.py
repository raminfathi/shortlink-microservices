import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import redis_client


@pytest.mark.asyncio
async def test_create_and_redirect_link():
    """
    Full lifecycle test for a link.
    """
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create Link
        long_url = "https://www.python.org/"
        response = await ac.post("/links", json={"long_url": long_url})

        assert response.status_code == 201
        data = response.json()
        short_id = data["short_link"].split("/")[-1]

        # 2. FIX: Manually add to Bloom Filter (Simulate Worker)
        # We access the raw client directly to avoid changing core-api source code
        client = await redis_client.get_client()
        await client.bf().add("bf:short_links", short_id)

        # 3. Test Redirect
        redirect_response = await ac.get(f"/{short_id}")

        assert redirect_response.status_code == 307
        assert redirect_response.headers["location"] == long_url


@pytest.mark.asyncio
async def test_get_stats_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/non_existent_id/stats")
        assert response.status_code == 404