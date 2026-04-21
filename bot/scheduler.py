import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from bot.config import JOKE_HOUR, JOKE_MINUTE, GROUP_CHAT_ID, TIMEZONE
from bot.jokes import get_next_joke
from bot.database import log_send

logger = logging.getLogger(__name__)


async def send_daily_joke(bot: Bot) -> None:
    joke = get_next_joke()
    try:
        await bot.send_message(chat_id=GROUP_CHAT_ID, text=f"😄 Анекдот дня:\n\n{joke}")
        log_send(chat_id=GROUP_CHAT_ID, message=joke)
        logger.info("Анекдот отправлен в чат %s", GROUP_CHAT_ID)
    except Exception:
        logger.exception("Ошибка при отправке анекдота")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_daily_joke,
        trigger=CronTrigger(hour=JOKE_HOUR, minute=JOKE_MINUTE, timezone=TIMEZONE),
        kwargs={"bot": bot},
        id="daily_joke",
        name="Ежедневный анекдот",
        misfire_grace_time=60,
        replace_existing=True,
    )
    logger.info("Планировщик: анекдот каждый день в %02d:%02d (%s)", JOKE_HOUR, JOKE_MINUTE, TIMEZONE)
    return scheduler
