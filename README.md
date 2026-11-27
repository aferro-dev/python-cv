# Python & LLM — backend da studiare

Un progetto eseguibile per prepararsi a un ruolo **Back-end developer — Python, LLM**.
Il caso d'uso è una knowledge base personale: registri un utente, inserisci documenti,
fai domande e ricevi risposte con fonti. La base precedente `custom_llm/` resta un
laboratorio separato per capire come funziona un Transformer.

## Avvio rapido

Richiede Python 3.13+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync --frozen
cp .env.example .env
uv run uvicorn main:app --reload
```

Apri http://localhost:8000/docs. In modalità `demo` non servono GPU, download di
modelli o servizi esterni. SQLite viene inizializzato all'avvio solo in sviluppo.

1. `POST /api/v1/auth/register`: `{"username":"andrea","password":"una-password-lunga"}`.
2. Copia `access_token` e premi **Authorize** in Swagger.
3. `POST /api/v1/documents`: `{"title":"Python","content":"FastAPI usa Pydantic per validare i dati."}`.
4. `POST /api/v1/chat`: `{"question":"Come usa Pydantic FastAPI?"}`.
5. Prova lista, paginazione, cancellazione e `/api/v1/chat/stream`.

Il login accetta JSON su `/api/v1/auth/token`. Lo schema è HTTP Bearer, non un
OAuth2 authorization server. Il demo restituisce estratti etichettati: non simula
un modello generativo e non misura la qualità di un vero LLM.

## Cosa contiene

| Area | Implementazione e cosa studiare |
| --- | --- |
| API | FastAPI, OpenAPI, dependency injection, app factory, lifespan, HTTP status |
| Contratti | Pydantic v2, constraint, extra vietati, DTO separati dai modelli ORM |
| Configurazione | pydantic-settings, `.env`, SecretStr, validazione produzione |
| Dati | SQLAlchemy 2 asincrono, sessione per richiesta, transazioni, indici, paginazione |
| Database | SQLite locale, PostgreSQL con asyncpg, migrazioni Alembic reversibili |
| Sicurezza | Argon2, JWT con scadenza/issuer/audience, ownership, CORS esplicito |
| RAG | Chunk sovrapposti, tokenizzazione Unicode, ranking BM25, top-k, fonti |
| LLM | Protocol, dependency injection, demo offline, AsyncOpenAI Responses, Hugging Face |
| Task in background | Celery + Redis, stato e risultati nel DB, retry/backoff, polling e cancellazione |
| Concorrenza | async/await, thread per lavoro bloccante, semaforo, timeout e retry SDK |
| Osservabilità | Request ID, log strutturati, metriche Prometheus, liveness/readiness |
| Qualità | pytest, isolamento DB, test API e failure path, coverage, Ruff, mypy, CI |
| Esecuzione | uv e lockfile, Docker non-root, Compose e PostgreSQL persistente |
| Reti neurali | Transformer character-level, causal attention, residual, LayerNorm, AdamW |

## Struttura degli endpoint

L'API segue l'organizzazione dei backend Node/Go vicini: cartelle per funzionalità,
registrazione delle rotte separata e **un file per endpoint**.

```text
app/api/
├── application.py       # create_app: configura e monta l'API
├── routes.py            # aggrega i router delle funzionalità
├── dependencies.py      # Session, current_user e CurrentUser
├── lifespan.py          # apertura e chiusura delle risorse
├── middleware.py        # request ID, log e metriche
├── auth/
│   ├── routes.py
│   ├── register.py
│   └── login.py
├── documents/
│   ├── routes.py
│   ├── create.py
│   ├── list.py
│   ├── read.py
│   ├── delete.py
│   └── service.py       # controllo ownership condiviso
├── chat/
│   ├── routes.py
│   ├── chat.py
│   ├── stream.py
│   └── service.py       # timeout e adattamento errori HTTP
├── tasks/
│   ├── routes.py
│   ├── submit.py
│   ├── list.py
│   ├── read.py
│   ├── cancel.py
│   └── service.py       # controllo ownership condiviso
└── health/
    ├── routes.py
    ├── root.py
    ├── live.py
    ├── ready.py
    └── metrics.py
```

Ogni `routes.py` associa metodo, percorso, schema di risposta e handler con
`APIRouter.add_api_route`, come un `routes.ts` Express o il registro Go.
Per aggiungere un endpoint crea il suo file e registralo nel router della
funzionalità. `from app.api import create_app` rimane l'entrypoint pubblico.
Il worker Celery è `app/tasks.py`; gli handler HTTP dei task sono in `app/api/tasks/`.

## Task in background con Celery

Puoi accodare domande con `POST /api/v1/tasks` e leggerne lo stato con
`GET /api/v1/tasks/{id}`. Docker Compose include Redis e il worker. Per avvio
locale, stati, cancellazione e retry leggi [la guida Celery](docs/TASKS.md).

## Provider reali

OpenAI: imposta `LLM_PROVIDER=openai`, `OPENAI_API_KEY` e `OPENAI_MODEL` in `.env`.
Il modello è configurabile; verifica disponibilità e costi per il tuo account.
Il client asincrono è condiviso per processo e chiuso nel lifespan. Lo SDK ritenta
errori transitori al massimo due volte; il timeout applicativo include la coda.
`store=False` disabilita la memorizzazione della response, non ogni possibile log
del fornitore. Domanda ed estratti selezionati vengono inviati al servizio.

Hugging Face locale:

```bash
uv sync --extra local
# in .env: LLM_PROVIDER=local
uv run uvicorn main:app
```

Il modello viene caricato al primo utilizzo, riusato e protetto da un lock.
CUDA è opzionale: su CPU sarà più lento. Ogni worker ha una propria copia del
modello. L'extra locale è pesante e non serve al normale backend o ai test.

## Verifica e migrazioni

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest --cov=app --cov-report=term-missing
```

Per passare da creazione automatica a migrazioni usa un database nuovo, imposta
`AUTO_CREATE_TABLES=false`, poi:

```bash
uv run alembic upgrade head
uv run alembic check
# dopo aver modificato i modelli, revisiona sempre il file generato:
uv run alembic revision --autogenerate -m "descrizione modifica"
```

Su un DB già creato con `create_all`, verifica lo schema prima di eseguire
`alembic stamp head`: stamp registra la versione, non applica modifiche.

Per Docker imposta un `JWT_SECRET` casuale in `.env`, poi `docker compose up --build`.
Compose avvia PostgreSQL e applica le migrazioni prima dell'API. La password del
DB nel compose è esclusivamente per sviluppo locale. `/health/ready` controlla
il DB; `/health/live` controlla il processo. `/metrics` è in formato Prometheus.

## Percorso di studio

Segui [la guida ragionata](docs/STUDIO.md): spiega flussi, scelte, esercizi,
domande da colloquio e limiti. Leggi prima `schemas.py`, poi il registro
`app/api/routes.py` e i singoli handler, quindi `db.py`, `security.py`,
`retrieval.py` e `llm.py`. Esegui i test mentre studi i comportamenti.

Laboratorio Transformer, con un corpus UTF-8 tuo sufficientemente lungo:

```bash
uv sync --extra local
uv run python -m custom_llm.train corpus.txt --steps 100 --output checkpoint.pt
```

Il training non parte durante un import. Salva pesi e vocabolario; non è un
instruction model né un sostituto dei provider RAG. I default sono impegnativi
su CPU: riduci batch, layer e iterazioni in `custom_llm/constants.py`.
