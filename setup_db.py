"""Одноразовый скрипт — создать таблицы в Supabase. Запускать один раз."""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]

client = create_client(url, key)

# Supabase не поддерживает CREATE TABLE через REST API напрямую.
# Таблицы нужно создавать через SQL Editor в Supabase Dashboard.
# Этот скрипт проверяет подключение и инициализирует строку joke_state.

print("Проверяем подключение к Supabase...")
try:
    res = client.table("joke_state").select("*").execute()
    rows = res.data
    if not rows:
        print("Таблица joke_state пуста — создаём начальную запись...")
        client.table("joke_state").insert({"id": 1, "idx": 0}).execute()
        print("joke_state инициализирована: id=1, idx=0")
    else:
        print(f"joke_state уже существует: {rows}")
except Exception as e:
    print(f"ОШИБКА: {e}")
    print("\nВозможно таблицы ещё не созданы.")
    print("Создайте их в Supabase Dashboard → SQL Editor:\n")
    print("""
CREATE TABLE joke_state (
    id  INTEGER PRIMARY KEY DEFAULT 1,
    idx INTEGER NOT NULL DEFAULT 0
);
INSERT INTO joke_state (id, idx) VALUES (1, 0);

CREATE TABLE schedules (
    id         SERIAL PRIMARY KEY,
    send_time  TIME NOT NULL,
    message    TEXT,
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE send_log (
    id          SERIAL PRIMARY KEY,
    sent_at     TIMESTAMPTZ DEFAULT NOW(),
    chat_id     BIGINT NOT NULL,
    message     TEXT NOT NULL,
    schedule_id INTEGER REFERENCES schedules(id)
);
""")
