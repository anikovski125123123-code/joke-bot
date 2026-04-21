# Joke Bot — Project Cheatsheet

## Суть проекта
Telegram-бот для группового чата, который отправляет анекдоты по расписанию.
Целевая аудитория: Артём и Петя.

## Инфраструктура
| Слой | Сервис |
|---|---|
| Хостинг | Railway (auto-deploy из GitHub main) |
| Репозиторий | GitHub |
| База данных | Supabase (PostgreSQL) |
| Бот | aiogram 3.x, long-polling |
| Планировщик | APScheduler (внутри процесса) |

> ВАЖНО: Railway имеет ephemeral filesystem. Любое состояние (joke_index, расписание, логи)
> хранится ТОЛЬКО в Supabase. Никаких .txt/.db файлов.

## Технологический стек
- **Python 3.11+**
- **aiogram 3.13.x** — Telegram Bot API
- **APScheduler 3.x** — cron-задачи внутри процесса
- **supabase 2.x** — Python-клиент для Supabase/PostgreSQL
- **python-dotenv** — загрузка переменных окружения
- **pytz** — часовые пояса
- **OpenAI API** — генерация анекдотов (Фаза 3)

## Структура проекта
```
bot anik 2/
├── bot/
│   ├── __init__.py
│   ├── main.py            # точка входа, инициализация
│   ├── config.py          # загрузка .env, константы
│   ├── database.py        # Supabase клиент + CRUD
│   ├── jokes.py           # пул анекдотов (индекс в Supabase)
│   ├── scheduler.py       # APScheduler, cron-отправка
│   └── handlers/
│       ├── __init__.py
│       ├── user.py        # /start, кнопка "нужна шутка" (Ф.3)
│       └── admin.py       # /schedule * (Фаза 2)
├── data/
│   └── jokes.json         # банк анекдотов (статика, в git)
├── railway.toml            # команда запуска для Railway
├── .gitignore
├── .env.example
├── requirements.txt
├── CLAUDE.md
├── PROJECT_IDEA.md
└── TECH_SPEC.md           # полная техническая спецификация
```

## Переменные окружения (.env / Railway Dashboard)
```
BOT_TOKEN=           # от @BotFather
ADMIN_ID=            # Telegram user_id администратора
GROUP_CHAT_ID=       # id группового чата (отрицательный для групп)
JOKE_TIME=13:00      # HH:MM, МСК (UTC+3)
SUPABASE_URL=        # https://xxxx.supabase.co
SUPABASE_KEY=        # service_role key
OPENAI_API_KEY=      # Фаза 3
```

## Схема Supabase (создать в SQL Editor)
```sql
CREATE TABLE joke_state (id INTEGER PRIMARY KEY DEFAULT 1, idx INTEGER DEFAULT 0);
INSERT INTO joke_state VALUES (1, 0);

CREATE TABLE schedules (
    id SERIAL PRIMARY KEY, send_time TIME NOT NULL,
    message TEXT, is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE send_log (
    id SERIAL PRIMARY KEY, sent_at TIMESTAMPTZ DEFAULT NOW(),
    chat_id BIGINT NOT NULL, message TEXT NOT NULL,
    schedule_id INTEGER REFERENCES schedules(id)
);
```

## Фазы разработки

### Фаза 1 — MVP
- Бот в групповом чате, отправляет анекдот по JOKE_TIME
- Индекс анекдота хранится в Supabase `joke_state`
- Команда `/start`

### Фаза 2 — Админка
- `/schedule add HH:MM [текст]` — добавить задание
- `/schedule list` — все задания
- `/schedule delete <id>` — удалить
- Расписание в Supabase `schedules`, APScheduler восстанавливает при старте

### Фаза 3 — AI по запросу
- Кнопка «Нужна шутка» → OpenAI API → новый анекдот
- Cooldown 5 минут

## Ключевые решения
| Риск | Решение |
|---|---|
| Railway ephemeral FS | Всё состояние в Supabase |
| Бот не отправляет вовремя | misfire_grace_time=60 + send_log |
| Supabase недоступен | try/except, логировать, не падать |
| Секреты в git | .gitignore + только Railway Dashboard |

## Команды разработки
```bash
pip install -r requirements.txt
python -m bot.main
```

## CI/CD
`git push origin main` → Railway автодеплой → логи в Railway Dashboard
