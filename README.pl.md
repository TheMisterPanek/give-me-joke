# joker

[English](README.md) | [Русский](README.ru.md) | [Polski](README.pl.md)

Wyszukuj gotowe dowcipy według znaczenia we własnej kolekcji. Ten sam algorytm
jest dostępny przez bota Telegram, API HTTP, narzędzie MCP i gotowy skill dla agenta.

Joker znajduje 15 tekstów według podobieństwa cosinusowego, porządkuje je według
pozytywnych reakcji i losuje jeden z najlepszych pięciu. Nie generuje dowcipów
ani nie wymaga dosłownego występowania słów z zapytania. Opis eksperymentu i jego
ograniczeń znajduje się w [docs/research.md](docs/research.md) po angielsku.

## Dane i licencja

Repozytorium zawiera kod na licencji MIT, dokumentację, adaptery i sztuczne
przykłady testowe. Nie zawiera rzeczywistych zbiorów danych, nazw źródłowych
kanałów lub kolekcji, gotowego indeksu ani danych dostępowych. Dodaj własną kolekcję.

Źródła przechowuj w `data/raw/`, indeks w `data/store/`, a prywatne parsery
w `data/parsers/`. Git ignoruje `data/`, `.env`, typowe formaty danych i archiwa.
Indeks zawiera teksty źródłowe, więc również nie należy go publikować.
Nazwy zależności umożliwiają odtworzenie środowiska; pobierane modele mają własne licencje.

## Szybki start

Potrzebujesz Pythona 3.12+, uv i działającego serwera Ollama. Używaj tego samego
modelu do indeksowania i zapytań: domyślnie `qwen3-embedding:0.6b`.

```bash
uv sync
ollama pull qwen3-embedding:0.6b
# Run ollama serve in another session or as a service.
uv run python -m ingest.dataset data/raw/export.json
```

Domyślny parser czyta eksport wiadomości Telegram w formacie JSON. Łączy fragmenty
formatowanego tekstu; jeden post staje się jednym rekordem. Pomija wiadomości
puste, techniczne i dokładne duplikaty. Automatycznie odczytuje reakcje.
Indeks jest zapisywany partiami. Ponowne uruchomienie oblicza wektory tylko dla
nowych tekstów i aktualizuje maksymalne oceny reakcji.

Sprawdzenie danych bez Ollama i bez zmiany indeksu:

```bash
uv run python -m ingest.dataset data/raw/export.json --validate-only
```

Sztuczny przykład z osobnym indeksem:

```bash
uv run python tools/make_demo.py
JOKER_STORE_DIR=data/demo/store uv run python -m ingest.dataset data/demo/export.json
JOKER_STORE_DIR=data/demo/store uv run python api.py
```

Komunikaty programu i materiały dla programistów są po angielsku. Znalezione
dowcipy zachowują język źródła; tłumaczenie programu nie zmienia danych ani indeksu.

## API HTTP

Z istniejącym indeksem:

```bash
uv run python api.py
```

Domyślny adres to `http://127.0.0.1:8080`. Token Telegram nie jest potrzebny.

```bash
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/joke \
  -H 'Content-Type: application/json' \
  -d '{"query":"a bug that refuses to be fixed"}'
```

Odpowiedź `POST /joke`:

```json
{"text":"The joke text…", "similarity":0.72, "reactions":35}
```

`query` musi zawierać od 1 do 4000 znaków. Kody błędów: `422` — nieprawidłowe
dane, `401` — nieprawidłowy klucz, `404` — brak odpowiednich dowcipów,
`503` — wyszukiwanie lub Ollama niedostępne. `GET /health` sprawdza proces
i załadowany indeks bez wywoływania modelu. Interaktywna dokumentacja API jest pod `/docs`.

| Zmienna środowiskowa | Wartość domyślna | Znaczenie |
| --- | --- | --- |
| `JOKER_STORE_DIR` | `data/store` | Indeks i oceny reakcji |
| `OLLAMA_HOST` | `http://localhost:11434` | Adres Ollama |
| `OLLAMA_EMBED_MODEL` | `qwen3-embedding:0.6b` | Model embeddingów |
| `JOKER_HTTP_HOST` | `127.0.0.1` | Adres nasłuchiwania HTTP |
| `JOKER_HTTP_PORT` | `8080` | Port HTTP |
| `JOKER_API_KEY` | pusta | Opcjonalny klucz Bearer dla `/joke` |

Jeżeli ustawisz `JOKER_API_KEY`, wysyłaj nagłówek `Authorization: Bearer <key>`.
Ustawienia z pliku można załadować przez `uv run --env-file .env python api.py`.
Dostęp zewnętrzny zabezpiecz kluczem i HTTPS przez reverse proxy.

## Bot Telegram

Z Ollama działającą na komputerze:

```bash
cp .env.example .env
# Set TELEGRAM_BOT_TOKEN in .env.
uv run --env-file .env python bot.py
```

Bot odpowiada na wiadomości tekstowe. `/start` i `/help` wyświetlają instrukcję.
Aby odbierać wszystkie wiadomości w grupach, wyłącz privacy mode w usłudze
tworzenia botów. Dla jednego tokenu uruchamiaj tylko jedną instancję polling.

## Kontenery Podman

Najpierw utwórz indeks na hoście. Kontener montuje go tylko do odczytu.
Dane i `.env` nie są dołączane do obrazu. Zbuduj obraz podstawowy:

```bash
podman build -t localhost/joker-bot:latest -f Containerfile .
```

Telegram z Ollama na hoście Linux:

```bash
bash run-bot.sh
podman logs -f joker-bot
```

Telegram lub HTTP z Ollama wewnątrz kontenera:

```bash
podman build -t localhost/joker-bot-vps:latest -f Containerfile.vps .
```

Wybierz tryb:

```bash
# Telegram: .env with TELEGRAM_BOT_TOKEN is required.
bash run-bot-vps.sh
podman logs -f joker-bot

# Or HTTP: .env is optional; no Telegram token is needed.
bash run-http.sh
podman logs -f joker-http
curl http://127.0.0.1:8080/health
```

HTTP jest publikowane tylko na interfejsie loopback hosta. Inny port:
`JOKER_HTTP_PORT=8081 bash run-http.sh`. Są to osobne tryby; do podstawowej
konfiguracji nie trzeba uruchamiać obu kontenerów.

Wbudowana Ollama korzysta z CPU i pobiera wybrany model przy pierwszym starcie.
Wolumen `joker-ollama-models` zachowuje model po ponownym utworzeniu kontenera.
Port Ollama nie jest publikowany; `OLLAMA_HOST` wskazuje wewnętrzny loopback.
`OLLAMA_KEEP_ALIVE=0` w `.env` zwalnia model po każdym zapytaniu.
Domyślnie Ollama pozostawia go w pamięci przez pięć minut.
Bot/API i indeks pozostają w pamięci.

Zatrzymanie: `podman stop joker-bot` lub `podman stop joker-http`.
Ponowny start: `podman start <name>`. Po zmianie `.env`, kodu lub ocen reakcji
zatrzymaj i usuń kontener, a następnie uruchom jego skrypt ponownie.
Start po restarcie serwera wymaga konfiguracji systemd/Quadlet.

Przeniesienie na inny host Linux o tej samej architekturze:

```bash
podman save -o joker-bot-vps.tar localhost/joker-bot-vps:latest
tar -czf joker-data.tar.gz data/store run-bot-vps.sh run-http.sh
ssh user@VPS 'mkdir -p ~/joker'
scp joker-bot-vps.tar joker-data.tar.gz user@VPS:~/joker/
# For Telegram, transfer .env separately over SSH.
```

Na nowym hoście:

```bash
cd ~/joker
podman load -i joker-bot-vps.tar
tar -xzf joker-data.tar.gz
bash run-http.sh  # Or bash run-bot-vps.sh with .env.
```

Wolumen modelu nie trafia do `podman save`; nowy host pobierze model ponownie.
Archiwum indeksu służy do prywatnego przenoszenia, nie do publikacji w Git.

## Własny parser

Nie trzeba zmieniać głównego kodu. Sprowadź źródło do następującego formatu rekordu:

```json
{"text":"One complete joke", "tags":["topic"], "reactions":12}
```

Wymagane jest tylko `text`: niepusty tekst. `tags` to lista tekstów, domyślnie
`[]`. `reactions` to nieujemna liczba całkowita pozytywnych reakcji, domyślnie `0`.
Nieznane pola są odrzucane. Autor adaptera określa granice dowcipów, czyszczenie
źródła i sposób przeliczenia ocen na `reactions`.

Dwie możliwości:

1. Przygotuj JSONL z jednym rekordem w wierszu:
   `uv run python -m ingest.dataset data/raw/jokes.jsonl --parser jsonl`.
2. Napisz funkcję Python `parse(path)`, która zwraca lub generuje przez `yield`
   słowniki tego formatu. Dobierz regex, CSV, XML lub inne narzędzie do danych wejściowych.

[examples/csv_parser.py](examples/csv_parser.py) to działający adapter CSV
z kolumnami `body`, `category` i `likes`. Skopiuj go do `data/parsers/my_parser.py`,
dostosuj pola i sprawdź wynik przed indeksowaniem:

```bash
uv run python -m ingest.dataset data/raw/source.csv \
  --parser data/parsers/my_parser.py:parse --validate-only
uv run python -m ingest.dataset data/raw/source.csv \
  --parser data/parsers/my_parser.py:parse
```

Obsługiwane są też importowalne moduły: `--parser my_package.my_parser:parse`.
Parser jest lokalnym kodem Python. Rekordy są sprawdzane podczas przetwarzania
partii. Błąd w późniejszym rekordzie nie usuwa zapisanych partii: popraw dane
i uruchom ponownie. Domyślne `--batch-size` wynosi 32.
Po zmianie ocen reakcji uruchom usługę ponownie.

## MCP i gotowy skill

Najpierw uruchom API HTTP. Adapter MCP udostępnia `find_joke(context)` przez
stdio i korzysta z API bez ładowania drugiego indeksu. Przykładowa konfiguracja
klienta — zastąp ścieżkę bezwzględną:

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

Jeżeli API wymaga klucza, ustaw też `JOKER_API_KEY` w środowisku klienta.
Narzędzie zwraca `text`, `similarity` i `reactions`.

[Skill Joker](skills/joker/SKILL.md) korzysta z MCP lub samodzielnego skryptu
Python, który nie wymaga zewnętrznych bibliotek:

```bash
JOKER_API_URL=http://127.0.0.1:8080 \
  python3 skills/joker/scripts/find_joke.py "a stubborn programming bug"
```

Skopiuj `skills/joker` do katalogu skills swojego agenta, na przykład:

```bash
# For an agent using ~/.claude/skills:
mkdir -p ~/.claude/skills
cp -R skills/joker ~/.claude/skills/
# Or an agent using ~/.codex/skills:
mkdir -p ~/.codex/skills
cp -R skills/joker ~/.codex/skills/
```

MCP nie dodaje żartów automatycznie — agent wykonuje instrukcje użytkownika.
Przykładowy dobrowolny tryb: „Jeśli zadanie pozostaje nierozwiązane, najpierw
uczciwie opisz wynik i przeszkodę. Potem, jeśli to odpowiednie, użyj Joker i dodaj
jeden dowcip. Nie przerywaj szukania rozwiązania tylko po to, aby znaleźć żart”.
Skill wysyła jedynie krótki temat, bez kodu, logów i całej rozmowy.

## Rozwój

```bash
uv run pytest -q
uv export --frozen --no-dev --no-emit-project -o requirements-bot.txt
```

`give-me-joke.py` to diagnostyczne CLI przeszukujące cały indeks i pokazujące
podobieństwo. Do wyników filtrowanych i uporządkowanych według reakcji używaj API lub bota.
