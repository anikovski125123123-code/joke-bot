import logging
from supabase import create_client, Client
from bot.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def get_joke_index() -> int:
    try:
        res = get_client().table("joke_state").select("idx").eq("id", 1).single().execute()
        return res.data["idx"]
    except Exception:
        logger.exception("Ошибка получения joke_index из Supabase, возвращаем 0")
        return 0


def set_joke_index(idx: int) -> None:
    try:
        get_client().table("joke_state").update({"idx": idx}).eq("id", 1).execute()
    except Exception:
        logger.exception("Ошибка сохранения joke_index в Supabase")


def log_send(chat_id: int, message: str, schedule_id: int | None = None) -> None:
    try:
        payload = {"chat_id": chat_id, "message": message}
        if schedule_id is not None:
            payload["schedule_id"] = schedule_id
        get_client().table("send_log").insert(payload).execute()
    except Exception:
        logger.exception("Ошибка записи в send_log")
