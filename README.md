# Gold Prices Fetcher

> Opinionated, production-oriented Playwright-based scraper demonstrating: concurrency, stealthy browser automation, scheduling with Celery, observability (Loki / Grafana), and persistence to Postgres shipped as a Dockerized, ops-ready system.

---

## TL;DR

This repo is a compact, production-minded proof-of-concept for robust web automation:

* Uses **Playwright** (with `playwright_stealth`) to scrape dynamic, JS-heavy sites.
* Scrapers are **modular** and **dynamically loaded** from `app/sites.json`.
* Concurrent, async scraping managed by `ScraperService` (asyncio + `asyncio.gather`).
* Scheduling & distributed execution via **Celery** (Redis broker/backend + Celery Beat schedule configured).
* Results persisted with **SQLAlchemy** to **Postgres**.
* Observability: structured JSON logs, Promtail + Loki + Grafana provisioning included.
* Portable: `Dockerfile` + `docker-compose.yml` for one-command local runs.

This project is intentionally engineered to be extended for tasks Firecrawl cares about: high-throughput browser automation, fingerprinting avoidance, proxying, and (optionally) an LLM-based extraction/normalization layer.

---

## Highlights / Why this will interest the Firecrawl team

* **Browser automation:** Playwright + `playwright_stealth` to reduce bot fingerprinting surface.
* **Concurrency & reliability:** async scrapers + structured error handling (screenshots saved on failures) and centralized tracing (`trace_id` attached to events).
* **Production readiness:** Dockerized services, DB init scripts, Celery scheduling, logging & monitoring with Loki/Grafana.
* **Modular design:** Add new site scrapers via `app/scraper/scrapers.py` and register them in `app/sites.json` — the service dynamically imports and executes scrapers.
* **Ops-friendly:** logs structured as JSON (designed to feed Loki), screenshots on failures (`errors_screenshoots`), and SQL schema migration via `app/db/init/001_init.sql`.

---

## Architecture (quick)

```
[ Celery Beat ] --> triggers --> [ Celery Worker(s) ] --> runs -> ScraperService
                                                   |--> Playwright (headless) -> site pages
                                                   |--> saves results -> Postgres
                                                   |--> logs -> stdout -> promtail -> Loki -> Grafana
                                                   |--> optional: Telegram notifications
```

Key components:

* `app/scraper/*` — contains the scrapers and `ScraperService` orchestration.
* `app/tasks.py` — Celery app + the scheduled `scrape_gold_price` task.
* `app/utils/playwright_utils.py` — helpers for robust page interaction (scrolling until visible, screenshots on failure, etc.).
* `app/db/*` — SQLAlchemy models and DB initialization SQL.
* `docker-compose.yml` — brings up Redis (broker), Postgres (persistence), Loki/Grafana (monitoring), and the worker.

---

## How it works (end-to-end)

1. `app/tasks.py` defines a Celery task (`scrape_gold_price`) and a beat schedule. Celery workers pick up tasks.
2. `ScraperService` (singleton) loads `app/sites.json`, instantiates site-specific scraper classes (e.g. `GoldPriceOrgScraper`) via dynamic import, and schedules them concurrently.
3. Each scraper uses Playwright (`async_playwright`) and `playwright_stealth` to create a stealthy browser context, navigates to the site, extracts content (via robust XPath+scroll helpers), and returns a sanitized result.
4. Results are written to Postgres (table: `public.gold_prices`) using SQLAlchemy.
5. Important events and errors are emitted via structured logging. On parse/selector failures, a screenshot is saved to `errors_screenshoots/` to speed debugging.
6. A Telegram alert helper exists to push a summary after each run (requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`).

---

## Run locally — recommended (Docker Compose)

This is the fastest way to reproduce the full environment (Redis, Postgres, Grafana/Loki, and the Celery worker):

1. Copy the example env and tweak if needed:

```bash
cp .env.template .env
# edit .env to set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID if you want notifications
```

2. Start everything:

```bash
# If you have modern Docker Compose plugin
docker compose up --build -d

# OR (older installations)
# docker-compose up --build
```

3. Wait for containers to be healthy. The Celery worker will register and run the periodic scraping task.

4. Visit Grafana at [http://localhost:3000](http://localhost:3000) (default admin/admin) to explore logs and prices dashboards (Grafana/Loki are provisioned).

Notes:

* Postgres is exposed on `5439:5432` by the provided compose file; the DB initialization SQL in `app/db/init/` will ensure the table exists.
* Redis is exposed on `6379:6379` for local connectivity.

---

## Configuration (.env)

Copy `.env.template` to `.env` and set the following values:

* `SERVICE_NAME` — service identifier
* `LOG_LEVEL` — `debug|info|warning|error`
* `LOG_DEST` — `stdout|file`
* `LOG_FILE_PATH` — path when `LOG_DEST=file`
* `REDIS_URL` — broker (defaults to `redis://redis:6379/0` in compose)
* `TELEGRAM_BOT_TOKEN` — optional, for Telegram alerts
* `TELEGRAM_CHAT_ID` — optional, for Telegram alerts
* `DATABASE_URL` — SQLAlchemy connection string (compose defaults to `postgresql+psycopg2://gold:gold@postgres:5432/gold`)

---

## Database

* SQL schema lives in `app/db/init/001_init.sql` and is mounted into Postgres when using docker-compose. It creates `public.gold_prices` and useful indexes.
* The SQLAlchemy model is `app/db/models.py` (`GoldPrice`).

---

## Observability

* Logs are collected as structured JSON; `promtail` + `loki` + `grafana` are included in the compose to provide a quick logs+dashboard experience.
* On parsing errors the code saves screenshots to `errors_screenshoots/` to make debugging selector issues fast.

---

## Project structure (key files)

```
app/
  main.py                 # one-off runner
  tasks.py                # celery tasks + schedule
  sites.json              # canonical list of sites + scraper class path
  scraper/
    service.py            # orchestrator (loads scrapers, runs concurrently)
    scrapers.py           # site-specific scrapers
  utils/
    playwright_utils.py   # helpers: scroll_until_visible, fetch_element_inner_html, screenshots
    logger.py             # structured log helper
    telegram.py           # Telegram push notifications
  db/
    db.py                 # SQLAlchemy engine + SessionLocal
    models.py             # GoldPrice model
    init/001_init.sql     # DB init SQL
Dockerfile
docker-compose.yml
.loki/promtail/grafana   # provisioning + configs
```

---

## Missing/Planned improvements (honest)

These are deliberate opportunities to take this from POC → production-grade crawler (great to discuss in an interview or paid trial):

* **Rotating proxies + credential rotation** (per-site proxy pools).
* **Advanced fingerprinting countermeasures**: canvas/webgl/noise, UA lifecycling, network-level fingerprinting mitigation.
* **Browser pool manager**: a shared pool of browser contexts (or Playwright Worker/Cluster) for efficiency at scale.
* **Generalized extraction**: lightweight LLM stage to convert HTML into LLM-ready, structured JSON or markdown (direct alignment with Firecrawl product).
* **End-to-end tests & CI**: add smoke tests for each site, CI workflows for linting & smoke runs in a controlled environment.

---

## How this aligns with the Firecrawl role

This repo demonstrates the exact fundamentals you’re hiring for:

* Experience with **headless browsers** and JS-heavy site scraping (Playwright + stealth).
* Production minded: **scheduling**, **retries**, **observable logs**, and **persistence**.
* Modular architecture that **scales** and can be extended to integrate LLMs/agents for extraction and normalization.

If you like, I can also prepare a short follow-up patch that implements any of the planned improvements above (proxy rotation, browser pool, or an LLM-based extraction step) as a demonstration for a paid trial.

Thanks!