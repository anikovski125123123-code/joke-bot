# Joke Bot — Техническая спецификация

## Инфраструктура

```
GitHub (main branch)
        │  push → auto-deploy
        ▼
   Railway.app
   (Python process, long-polling)
        │  async queries
        ▼
  Supabase (PostgreSQL)
  joke_state | schedules | send_log
```

| Слой | Сервис | Роль |
|---|---|---|
| Хостинг | Railway | Запуск Python-процесса 24/7 |
| CI/CD | GitHub Actions / Railway Git Integration | Auto-deploy при пуше в `main` |
| База данных | Supabase (PostgreSQL) | Состояние бота, расписание, логи |
| Бот | aiogram 3.x | Telegram Bot API |
| Планировщик | APScheduler | Cron-задачи внутри процесса |

---

## Почему Supabase, а не SQLite

Railway имеет **ephemeral filesystem**: при каждом деплое или перезапуске контейнера
все файлы (`.txt`, `.db`, `.json`-индексы) стираются. Любое состояние должно жить
в PostgreSQL (Supabase). Это касается в том числе `joke_index.txt` из текущего `jokes.py`.

---

## Схема базы данных (Supabase / PostgreSQL)

### Таблица `joke_state`
Хранит текущий индекс выданных анекдотов. Одна строка (singleton).
```sql
CREATE TABLE joke_state (
    id      INTEGER PRIMARY KEY DEFAULT 1,
    idx     INTEGER NOT NULL DEFAULT 0
);
INSERT INTO joke_state (id, idx) VALUES (1, 0);
```

### Таблица `schedules` (Фаза 2)
Расписание отправки сообщений.
```sql
CREATE TABLE schedules (
    id         SERIAL PRIMARY KEY,
    send_time  TIME NOT NULL,           -- UTC+3 (МСК)
    message    TEXT,                    -- NULL = брать из jokes.json
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Таблица `send_log`
Аудит каждой отправки.
```sql
CREATE TABLE send_log (
    id          SERIAL PRIMARY KEY,
    sent_at     TIMESTAMPTZ DEFAULT NOW(),
    chat_id     BIGINT NOT NULL,
    message     TEXT NOT NULL,
    schedule_id INTEGER REFERENCES schedules(id)
);
```

---

## Переменные окружения

Задаются в Railway Dashboard → Variables (никогда не коммитятся в git).

```
# Telegram
BOT_TOKEN=           # от @BotFather
ADMIN_ID=            # Telegram user_id администратора (int)
GROUP_CHAT_ID=       # id группового чата (int, отрицательный для групп)

# Расписание
JOKE_TIME=13:00      # HH:MM, часовой пояс МСК (UTC+3)

# Supabase
SUPABASE_URL=        # https://xxxx.supabase.co
SUPABASE_KEY=        # service_role key (НЕ anon key — нужны права на запись)

# Фаза 3
OPENAI_API_KEY=      # для AI-генерации анекдотов
```

---

## Структура файлов (финальная)

```
bot anik 2/
├── bot/
│   ├── __init__.py
│   ├── main.py            # точка входа
│   ├── config.py          # загрузка .env
│   ├── database.py        # Supabase клиент + CRUD
│   ├── jokes.py           # пул анекдотов (индекс в Supabase)
│   ├── scheduler.py       # APScheduler
│   └── handlers/
│       ├── __init__.py
│       ├── user.py        # /start, кнопка "нужна шутка" (Фаза 3)
│       └── admin.py       # /schedule * команды (Фаза 2)
├── data/
│   └── jokes.json         # банк анекдотов (статика, в git)
├── railway.toml            # конфигурация Railway
├── .gitignore
├── .env.example
├── requirements.txt
├── CLAUDE.md
├── PROJECT_IDEA.md
└── TECH_SPEC.md
```

---

## CI/CD: GitHub → Railway

1. Создать репозиторий на GitHub (публичный или приватный)
2. В Railway: New Project → Deploy from GitHub repo → выбрать репозиторий
3. Railway автоматически деплоит при каждом `git push origin main`
4. Переменные окружения задаются ТОЛЬКО в Railway Dashboard (не в коде)
5. `railway.toml` указывает команду запуска и версию Python

### railway.toml
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python -m bot.main"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

---

## Стек зависимостей

```
aiogram==3.13.1        # Telegram Bot API
APScheduler==3.10.4    # планировщик cron-задач
supabase==2.10.0       # Supabase Python client (asyncio-совместим)
python-dotenv==1.0.1   # загрузка .env
pytz==2024.1           # часовые пояса для APScheduler
```

---

## Ключевые архитектурные решения

| Решение | Обоснование |
|---|---|
| Supabase вместо SQLite | Railway ephemeral FS — SQLite не переживает рестарт |
| joke_index в БД | По той же причине — `joke_index.txt` стирается при деплое |
| long-polling, не webhook | Проще запустить на Railway без настройки домена; достаточно для малой аудитории |
| APScheduler внутри процесса | Не нужен отдельный воркер/Redis; достаточно для 1 задачи |
| `service_role` key Supabase | Нужны права на INSERT/UPDATE без RLS-ограничений |
| `misfire_grace_time=60` | APScheduler не пропустит задачу если процесс стартовал с задержкой до 60 сек |

---

## Что изменить в уже написанном коде

| Файл | Проблема | Исправление |
|---|---|---|
| `bot/jokes.py` | `joke_index.txt` — стирается на Railway | Читать/писать индекс в Supabase (`joke_state`) |
| `bot/config.py` | Нет Supabase переменных | Добавить `SUPABASE_URL`, `SUPABASE_KEY` |
| `requirements.txt` | SQLite/aiosqlite, нет supabase | Заменить на `supabase==2.10.0`, добавить `pytz` |
| — | Нет `railway.toml` | Создать |
| — | Нет `.gitignore` | Создать |

---

## Риски и митигация (обновлено)

| Риск | Решение |
|---|---|
| Бот не отправляет вовремя | `misfire_grace_time=60` + `send_log` для аудита |
| Потеря состояния при рестарте | Всё состояние в Supabase, FS не используется |
| Supabase недоступен | Логировать ошибку, пропустить отправку, не падать |
| Секреты попали в git | `.gitignore` для `.env`, переменные только в Railway Dashboard |
| Railway free tier sleep | Выбрать план с Hobby ($5/мес) или настроить keep-alive |

---

## Порядок первого деплоя

1. `git init && git remote add origin <github_url>`
2. Задать все переменные в Railway Dashboard
3. Выполнить SQL для создания таблиц в Supabase SQL Editor
4. `git push origin main` → Railway подхватывает и деплоит
5. Проверить логи Railway: бот должен написать "Бот запущен"
