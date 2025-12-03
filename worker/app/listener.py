import asyncio
import qrcode
import os
from .database import redis_client
from .config import settings, logger


# --- پردازشگر ۱: ساخت QR Code ---
async def process_qr_job(message_id: str, message_data: dict) -> bool:
    logger.info(f"--- PROCESSING QR JOB: {message_id} ---")
    try:
        short_id = message_data.get('short_id')
        long_url = message_data.get('long_url')

        if not short_id or not long_url:
            return False

        filename = f"{short_id}.png"
        save_path = os.path.join(settings.MEDIA_PATH, filename)

        img = qrcode.make(long_url)
        img.save(save_path)

        hash_key = f"data:{short_id}"
        web_path = f"/media/{filename}"
        await redis_client.set_hash_field(hash_key, "qr_code_path", web_path)

        logger.info(f"QR code generated for {short_id}")
        return True
    except Exception as e:
        logger.error(f"QR Job failed: {e}")
        return False


# --- پردازشگر ۲: ثبت آمار (جدید) ---
async def process_analytics_job(message_id: str, message_data: dict) -> bool:
    logger.info(f"--- PROCESSING ANALYTICS JOB: {message_id} ---")
    try:
        short_id = message_data.get('short_id')
        if not short_id:
            return False

        # کلید هش: data:abc
        hash_key = f"data:{short_id}"
        await redis_client.increment_hash_field(hash_key, "total_clicks", 1)
        leaderboard_key = "leaderboard:top_links"
        await redis_client.update_leaderboard(leaderboard_key, short_id, 1)

        logger.info(f"Analytics tracked for {short_id}.")
        return True
    except Exception as e:
        logger.error(f"Analytics Job failed: {e}")
        return False



# --- حلقه مصرف‌کننده عمومی (Generic Consumer Loop) ---
async def consume_stream(stream_name: str, group_name: str, processor_func):
    """
    یک حلقه بی‌نهایت که به یک استریم خاص گوش می‌دهد و
    پیام‌ها را به تابع پردازشگر (processor_func) می‌دهد.
    """
    try:
        # ایجاد گروه مصرف‌کننده
        await redis_client.create_consumer_group(stream_name, group_name)
        logger.info(f"Listening on '{stream_name}' as '{group_name}'...")

        while True:
            # خواندن پیام
            message_id, message_data = await redis_client.read_stream_group(
                stream_name,
                group_name,
                settings.CONSUMER_NAME
            )

            if message_id and message_data:
                # پردازش پیام با تابع مربوطه
                success = await processor_func(message_id, message_data)

                if success:
                    # تأیید پیام
                    await redis_client.acknowledge_message(stream_name, group_name, message_id)
    except Exception as e:
        logger.error(f"Consumer loop for {stream_name} failed: {e}")


# --- نقطه شروع اصلی ---
async def listen_for_jobs():
    """
    اجرای همزمان تمام شنونده‌ها
    """
    # اطمینان از اتصال اولیه
    await redis_client.get_client()

    # اجرای دو وظیفه (Task) به صورت همزمان (Parallel/Concurrent)
    await asyncio.gather(
        # شنونده ۱: QR Code
        consume_stream(
            settings.QR_CODE_JOBS_STREAM,
            settings.QR_CODE_CONSUMER_GROUP,
            process_qr_job
        ),
        # شنونده ۲: Analytics (جدید)
        consume_stream(
            settings.ANALYTICS_STREAM_NAME,
            settings.ANALYTICS_CONSUMER_GROUP,
            process_analytics_job
        )
    )