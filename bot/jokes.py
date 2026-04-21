import json
import logging
from pathlib import Path

from bot.database import get_joke_index, set_joke_index

logger = logging.getLogger(__name__)

_JOKES_FILE = Path(__file__).parent.parent / "data" / "jokes.json"


def _load_jokes() -> list[str]:
    with open(_JOKES_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_next_joke() -> str:
    jokes = _load_jokes()
    if not jokes:
        return "Анекдоты закончились — скоро пополним!"

    index = get_joke_index() % len(jokes)
    joke = jokes[index]
    set_joke_index(index + 1)

    logger.info("Выдан анекдот #%d из %d", index + 1, len(jokes))
    return joke
