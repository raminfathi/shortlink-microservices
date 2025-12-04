import asyncio
import qrcode
import os
from .database import redis_client
from .config import settings, logger


# --- Processor 1: QR Code Generation ---
async def process_qr_job(message_id: str, message_data: dict) -> bool:
    logger.info(f"--- PROCESSING QR JOB: {message_id} ---")
    try:
        short_id = message_data.get('short_id')
        long_url = message_data.get('long_url')

        if not short_id or not long_url:
            return False

        filename = f"{short_id}.png"
        save_path = os.path.join(settings.MEDIA_PATH, filename)

        # Generate QR code
        img = qrcode.make(long_url)
        img.save(save_path)

        # Save path to Redis Hash
        hash_key = f"data:{short_id}"
        web_path = f"/media/{filename}"
        await redis_client.set_hash_field(hash_key, "qr_code_path", web_path)

        bf_key = "bf:short_links"
        await redis_client.add_to_bloom_filter(bf_key, short_id)
        logger.info(f"QR code generated for {short_id}")
        return True
    except Exception as e:
        logger.error(f"QR Job failed: {e}")
        return False


# --- Processor 2: Analytics Tracking (Updated for TimeSeries) ---
async def process_analytics_job(message_id: str, message_data: dict) -> bool:
    logger.info(f"--- PROCESSING ANALYTICS JOB: {message_id} ---")
    try:
        short_id = message_data.get('short_id')
        user_ip = message_data.get('ip')

        if not short_id:
            return False

        # 1. Increment counter in Hash (Existing)
        hash_key = f"data:{short_id}"
        await redis_client.increment_hash_field(hash_key, "total_clicks", 1)

        # 2. Update Leaderboard (Existing)
        leaderboard_key = "leaderboard:top_links"
        await redis_client.update_leaderboard(leaderboard_key, short_id, 1)

        # VVV --- 3. Add to TimeSeries (NEW Phase 8) --- VVV
        # Key format: ts:clicks:{short_id}
        ts_key = f"ts:clicks:{short_id}"

        # Retention: Keep data for 7 days (7 * 24 * 60 * 60 * 1000 ms = 604800000 ms)
        await redis_client.add_timeseries_point(ts_key, value=1, retention_ms=604800000)
        # ^^^ ------------------------------------------ ^^^
        if user_ip:
            # Key format: uv:{short_id} (uv = Unique Visitors)
            uv_key = f"uv:{short_id}"
            await redis_client.add_to_hyperloglog(uv_key, user_ip)
        logger.info(f"Analytics tracked for {short_id} (Hash, Leaderboard, TimeSeries).")
        return True
    except Exception as e:
        logger.error(f"Analytics Job failed: {e}")
        return False


# --- Generic Consumer Loop ---
async def consume_stream(stream_name: str, group_name: str, processor_func):
    """
    Infinite loop to listen to a specific stream and pass messages to a processor function.
    """
    try:
        # Create consumer group if not exists
        await redis_client.create_consumer_group(stream_name, group_name)
        logger.info(f"Listening on '{stream_name}' as '{group_name}'...")

        while True:
            # Read new messages
            message_id, message_data = await redis_client.read_stream_group(
                stream_name,
                group_name,
                settings.CONSUMER_NAME
            )

            if message_id and message_data:
                # Process message
                success = await processor_func(message_id, message_data)

                if success:
                    # Acknowledge message
                    await redis_client.acknowledge_message(stream_name, group_name, message_id)
    except Exception as e:
        logger.error(f"Consumer loop for {stream_name} failed: {e}")


# --- Main Entry Point ---
async def listen_for_jobs():
    """
    Run all listeners concurrently.
    """
    # Ensure Redis connection
    await redis_client.get_client()

    # Run tasks concurrently
    await asyncio.gather(
        # Listener 1: QR Code
        consume_stream(
            settings.QR_CODE_JOBS_STREAM,
            settings.QR_CODE_CONSUMER_GROUP,
            process_qr_job
        ),
        # Listener 2: Analytics
        consume_stream(
            settings.ANALYTICS_STREAM_NAME,
            settings.ANALYTICS_CONSUMER_GROUP,
            process_analytics_job
        )
    )