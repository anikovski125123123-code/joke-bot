import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
ADMIN_ID: int = int(os.environ["ADMIN_ID"])
GROUP_CHAT_ID: int = int(os.environ["GROUP_CHAT_ID"])

JOKE_TIME: str = os.getenv("JOKE_TIME", "13:00")
JOKE_HOUR, JOKE_MINUTE = (int(x) for x in JOKE_TIME.split(":"))

TIMEZONE = "Europe/Moscow"

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
