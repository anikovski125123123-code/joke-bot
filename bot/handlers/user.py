from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import JOKE_HOUR, JOKE_MINUTE

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        f"Привет! 👋\n"
        f"Я бот с анекдотами. Каждый день в {JOKE_HOUR:02d}:{JOKE_MINUTE:02d} (МСК) "
        f"я буду присылать свежий анекдот в этот чат.\n\n"
        f"Ждите — скучно не будет! 😄"
    )
