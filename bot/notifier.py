import httpx
from loguru import logger
from . import config

async def send_telegram_message(message: str, use_html: bool = True):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning(" Telegram not configured - skipping notification")
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
    }

    if use_html:
        payload["parse_mode"] = "HTML"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)

            if response.status_code == 200:
                logger.info(" Telegram message sent successfully")
            else:
                logger.error(f" Telegram API error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f" Failed to send Telegram message: {e}")


async def notify_job_seen():
    message = " <b>I see a job!</b>\nClaiming now..."
    await send_telegram_message(message, use_html=True)


async def notify_job_claimed(job_description: str):
    message = f" <b>Job claimed successfully!</b>\n\n📋 <b>Description:</b>\n{job_description}"
    await send_telegram_message(message, use_html=True)


async def notify_error(error_message: str):
    message = f" Bot Error:\n{error_message}"
    await send_telegram_message(message, use_html=False)


async def notify_startup():
    await send_telegram_message(" <b>Bot started and running 24/7!</b>", use_html=True)