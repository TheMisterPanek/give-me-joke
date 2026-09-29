# joker

[English](README.md) | [Русский](README.ru.md) | [Polski](README.pl.md)

Поиск готовых анекдотов по смыслу в собственной коллекции. Один алгоритм
доступен через Telegram-бота, HTTP API и MCP. Есть готовый skill для агента.

Сервис выбирает 15 текстов по косинусной близости, оставляет пять с лучшими
положительными реакциями и возвращает случайный из этих пяти. Не генерирует
анекдоты и не использует точные слова запроса как обязательное условие.
Описание эксперимента и ограничений: [docs/research.md](docs/research.md).

Сообщения программы, логи и документация для разработчиков — на английском.
Найденные анекдоты сохраняют язык исходника; перевод кода не меняет датасет и индекс.

## Данные и публикация

Репозиторий содержит код под MIT, документацию, адаптеры и искусственные
тестовые примеры. Реальных датасетов, названий исходных каналов/сборников,
готового индекса и токенов здесь нет. Добавляйте свою коллекцию локально.

Храните исходники в `data/raw/`, индекс — в `data/store/`, собственные
непубликуемые парсеры — в `data/parsers/`. `data/`, `.env`, распространённые
форматы датасетов и архивы исключены из Git. Индекс содержит исходные тексты,
поэтому его тоже не включают в публичный репозиторий. Названия программных
зависимостей ниже нужны для воспроизводимого запуска; модели не входят в лицензию кода.

## Быстрый старт

Нужны Python 3.12+, uv и работающая Ollama. Для всех запросов используйте ту же
модель, с которой построен индекс: по умолчанию `qwen3-embedding:0.6b`.

```bash
uv sync
ollama pull qwen3-embedding:0.6b
# В другой сессии/службе должна работать ollama serve.
uv run python -m ingest.dataset data/raw/export.json
```

По умолчанию это экспорт сообщений Telegram в JSON. Форматированный текст
объединяется, одно сообщение становится одной записью; пустые, служебные
сообщения и точные дубли пропускаются. Реакции извлекаются автоматически.
Индекс сохраняется пакетами, повторный запуск добавляет только новые тексты
и обновляет максимальные оценки реакций без повторных embeddings.

Проверить формат без Ollama и изменения индекса:

```bash
uv run python -m ingest.dataset data/raw/export.json --validate-only
```

Для проверки без своего датасета создайте искусственный пример. Команда ниже
использует отдельный индекс и не меняет основной:

```bash
uv run python tools/make_demo.py
JOKER_STORE_DIR=data/demo/store uv run python -m ingest.dataset data/demo/export.json
JOKER_STORE_DIR=data/demo/store uv run python api.py
```

## HTTP API

С существующим индексом:

```bash
uv run python api.py
```

По умолчанию адрес — `http://127.0.0.1:8080`. Токен Telegram не нужен.

```bash
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/joke \
  -H 'Content-Type: application/json' \
  -d '{"query":"не получается исправить ошибку в программе"}'
```

Ответ `POST /joke`:

```json
{"text":"Текст анекдота…", "similarity":0.72, "reactions":35}
```

`query` — непустая строка до 4000 символов. Ошибки: `422` — неверный запрос,
`401` — неверный ключ, `404` — нет подходящих текстов, `503` — ошибка поиска/Ollama.
`GET /health` проверяет процесс и загруженный индекс, не вызывает модель.
Интерактивная схема API доступна на `/docs`.

Переменные окружения:

| Переменная | По умолчанию | Назначение |
| --- | --- | --- |
| `JOKER_STORE_DIR` | `data/store` | Индекс и оценки реакций |
| `OLLAMA_HOST` | `http://localhost:11434` | Адрес Ollama |
| `OLLAMA_EMBED_MODEL` | `qwen3-embedding:0.6b` | Модель индекса и запросов |
| `JOKER_HTTP_HOST` | `127.0.0.1` | Адрес прослушивания HTTP |
| `JOKER_HTTP_PORT` | `8080` | Порт HTTP |
| `JOKER_API_KEY` | пусто | Необязательный Bearer-ключ для `/joke` |

Если `JOKER_API_KEY` задан, клиент передаёт `Authorization: Bearer <key>`.
Для загрузки настроек из файла можно использовать `uv run --env-file .env python api.py`.
Для внешнего доступа используйте ключ и HTTPS через reverse proxy.

## Telegram-бот

С Ollama на компьютере:

```bash
cp .env.example .env
# Укажите TELEGRAM_BOT_TOKEN в .env.
uv run --env-file .env python bot.py
```

Бот отвечает на текстовые сообщения, `/start` и `/help` показывают подсказку.
В группах для получения всех сообщений отключите privacy mode у сервиса создания ботов.
Один токен должен обслуживать один запущенный экземпляр polling-бота.

## Контейнеры Podman

Индекс заранее создаётся на хосте и подключается в режиме чтения. Данные и
`.env` не включаются в образ. Сборка базового образа:

```bash
podman build -t localhost/joker-bot:latest -f Containerfile .
```

Telegram с Ollama на хосте (Linux):

```bash
bash run-bot.sh
podman logs -f joker-bot
```

Для Telegram или HTTP с Ollama внутри контейнера:

```bash
podman build -t localhost/joker-bot-vps:latest -f Containerfile.vps .
```

Выберите режим:

```bash
# Telegram, .env с TELEGRAM_BOT_TOKEN обязателен:
bash run-bot-vps.sh
podman logs -f joker-bot

# Или HTTP, .env необязателен, токен Telegram не нужен:
bash run-http.sh
podman logs -f joker-http
curl http://127.0.0.1:8080/health
```

HTTP публикуется только на loopback хоста. Другой порт:
`JOKER_HTTP_PORT=8081 bash run-http.sh`. Это отдельные режимы; запускать оба
контейнера одновременно для проверки не требуется.

Встроенная Ollama работает на CPU и скачивает выбранную модель при первом
запуске. Модель сохраняется в томе `joker-ollama-models`, без повторной загрузки
при пересоздании контейнера. Ollama не публикует свой порт наружу.
`OLLAMA_HOST` в этом образе задаётся на внутренний loopback.
`OLLAMA_KEEP_ALIVE=0` в `.env` выгружает модель после каждого запроса;
по умолчанию Ollama держит её пять минут. Бот/API и индекс остаются в памяти.

Остановить: `podman stop joker-bot` или `podman stop joker-http`.
Снова запустить: `podman start <name>`. После изменения `.env`, кода или
оценок реакций пересоздайте контейнер: stop, rm, повторный запуск скрипта.
Для запуска после перезагрузки сервера настройте systemd/Quadlet.

Перенос на другой Linux-хост той же архитектуры:

```bash
podman save -o joker-bot-vps.tar localhost/joker-bot-vps:latest
tar -czf joker-data.tar.gz data/store run-bot-vps.sh run-http.sh
ssh user@VPS 'mkdir -p ~/joker'
scp joker-bot-vps.tar joker-data.tar.gz user@VPS:~/joker/
# Для Telegram отдельно перенесите .env по SSH.
```

На новом хосте:

```bash
cd ~/joker
podman load -i joker-bot-vps.tar
tar -xzf joker-data.tar.gz
bash run-http.sh  # Или bash run-bot-vps.sh с .env.
```

Модель не входит в `podman save`: на новом хосте она скачается заново.
Архив индекса предназначен для личного переноса, не для публичного Git.

## Свой формат: bring your own parser

Основной код менять не нужно. Достаточно привести источник к контракту записи:

```json
{"text":"Полный текст одного анекдота", "tags":["тема"], "reactions":12}
```

Обязателен только `text`: непустая строка. `tags` — список строк (по умолчанию
`[]`), `reactions` — целое неотрицательное число положительных реакций (по умолчанию `0`).
Неизвестные поля отвергаются. Границы анекдотов, очистку своего источника и
перевод его оценок в `reactions` определяет автор адаптера.

Два способа подключения:

1. Подготовить JSONL, по одной JSON-записи на строку:
   `uv run python -m ingest.dataset data/raw/jokes.jsonl --parser jsonl`.
2. Написать Python-функцию `parse(path)`, возвращающую или выдающую через
   `yield` словари этого контракта. Регулярки, CSV, XML и другие средства
   разбора выбираются внутри функции под конкретный источник.

Рабочий CSV-адаптер с колонками `body`, `category`, `likes` находится в
[examples/csv_parser.py](examples/csv_parser.py). Скопируйте его в
`data/parsers/my_parser.py`, адаптируйте поля и проверьте:

```bash
uv run python -m ingest.dataset data/raw/source.csv \
  --parser data/parsers/my_parser.py:parse --validate-only
uv run python -m ingest.dataset data/raw/source.csv \
  --parser data/parsers/my_parser.py:parse
```

Также поддерживается `--parser my_package.my_parser:parse` для импортируемого
модуля. Парсер — локальный Python-код, а не часть данных. Записи проверяются
перед добавлением каждого пакета; если источник содержит ошибку позже,
уже сохранённые пакеты остаются и запуск можно продолжить после исправления.
`--batch-size` по умолчанию 32. Обновлённые реакции применяются после перезапуска сервиса.

## MCP и готовый skill

Запустите HTTP API любым способом выше. MCP-адаптер обращается к нему и
предоставляет инструмент `find_joke(context)`; второй индекс в память не загружается.
Конфигурация для клиента со stdio MCP (замените абсолютный путь):

```json
{
  "mcpServers": {
    "joker": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/joker", "python", "mcp_server.py"],
      "env": {"JOKER_API_URL":"http://127.0.0.1:8080"}
    }
  }
}
```

При защите API передайте также `JOKER_API_KEY` через окружение клиента.
Вызов инструмента возвращает `text`, `similarity`, `reactions`.

Готовый skill: [skills/joker/SKILL.md](skills/joker/SKILL.md). Он работает
через MCP или автономный Python-скрипт без внешних зависимостей:

```bash
JOKER_API_URL=http://127.0.0.1:8080 \
  python3 skills/joker/scripts/find_joke.py "упрямый баг в программе"
```

Скопируйте папку `skills/joker` в каталог skills своего агента, например:

```bash
# Для агента с каталогом ~/.claude/skills:
mkdir -p ~/.claude/skills
cp -R skills/joker ~/.claude/skills/
# Или для агента с каталогом ~/.codex/skills:
mkdir -p ~/.codex/skills
cp -R skills/joker ~/.codex/skills/
```

MCP не добавляет шутки самостоятельно: это делает агент по инструкции пользователя.
Пример добровольного режима: «Если задача остаётся нерешённой, сначала честно
опиши результат и препятствие; затем, если уместно, используй Joker и добавь
один анекдот. Не прекращай поиск решения ради шутки».
Skill не отправляет в API код, логи или всю беседу — только краткую тему.

## Разработка

```bash
uv run pytest -q
uv export --frozen --no-dev --no-emit-project -o requirements-bot.txt
```

CLI `give-me-joke.py` остаётся диагностическим поиском по всему индексу с
оценками близости; для фильтрованной выдачи по реакциям используйте API или бота.
