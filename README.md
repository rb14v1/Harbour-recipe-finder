# Recipe Finder

Full-stack AI recipe search app: React + Django REST Framework + PostgreSQL
(pgvector) with an SQLite dev fallback and a stub-by-default AI layer.

## Stack

- Backend: Django 5 + Django REST Framework + Simple JWT
- Database: PostgreSQL + pgvector (production), SQLite (dev/local/test)
- AI: OpenAI embeddings + chat completions when `OPENAI_API_KEY` is set;
  deterministic stub mode otherwise (no key, no network, no cost)
- Frontend: React + Vite + TypeScript

## AI / stub mode

This app runs in two modes, chosen purely by whether `OPENAI_API_KEY` is set
in the environment:

- **Stub mode (default, no key needed)**: `apps/common/ai.py` generates
  reproducible pseudo-random embedding vectors (SHA-256-seeded) and
  templated text suggestions. This is NOT semantically meaningful search —
  two recipes about "chicken" will not be close together in stub-vector
  space the way they would be with a real embedding model. It exists purely
  so the full pipeline (storage, ranking, API shape, frontend) is testable
  without any API key, network access, or cost.
- **Real mode**: set `OPENAI_API_KEY` (and optionally `OPENAI_EMBEDDING_MODEL`,
  `OPENAI_CHAT_MODEL`) to get real embeddings and real grounded suggestions.

The frontend search page shows a visible "running in stub mode" banner
whenever the backend's suggestion text contains the stub marker.

## Database backend switch

Set `USE_SQLITE=True` (default for local dev, see `.env.example`) to run on
SQLite with zero external dependencies — the embedding column becomes a
plain JSON list of floats in this mode. Set `USE_SQLITE=False` and configure
`POSTGRES_*` to run against a real Postgres server. That server **must**
have the `pgvector` extension installed (`CREATE EXTENSION vector` is run
automatically by the first recipes migration, and will fail loudly if the
extension isn't installed — this is expected behaviour, not a bug).

> Note: pgvector is not installed on the Postgres instance available in this
> development environment, and there is no admin access to install it here.
> The Postgres/pgvector code path has been written to be correct per the
> pgvector-django API, but has only been verified against SQLite locally.
> Docker Compose (`docker-compose.yml`) uses the `pgvector/pgvector:pg16`
> image, which ships the extension pre-installed, for a from-scratch
> deployment.

## Backend setup (local, SQLite)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
set USE_SQLITE=True          # Windows cmd; $env:USE_SQLITE="True" in PowerShell
# DJANGO_SECRET_KEY (and POSTGRES_PASSWORD for Postgres) must be set in the environment or .env
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py runserver
```

The `migrate` step runs a data migration that seeds a demo user
(credentials are supplied via environment variables, not documented here) and ~13 sample recipes across several
cuisines, each with a stub embedding computed at seed time. The seed
migration is idempotent — running `migrate` again does not duplicate rows.

## Backend setup (Postgres + pgvector, e.g. via Docker Compose)

```bash
docker compose up --build
```

This runs Postgres (pgvector image), applies migrations (including
`CREATE EXTENSION vector` and the seed data), and serves the API.

## Frontend setup

```bash
cd frontend
npm install
npm run dev      # local dev server on :5173
npm run build    # production build
```

Configure `VITE_API_BASE_URL` (see `.env.example`) if the backend isn't at
the default `http://localhost:8000/api`.

## API

- `POST /api/auth/register/` — email, password, first_name, last_name
- `POST /api/auth/login/` — email, password -> access/refresh JWT
- `POST /api/auth/refresh/` — refresh -> new access token
- `POST /api/auth/logout/` — refresh -> blacklists it
- `GET  /api/auth/me/` — current user
- `GET/POST /api/recipes/`, `GET/PUT/PATCH/DELETE /api/recipes/{id}/`
- `POST /api/search/` — `{"query": "...", "top_k": 5}` ->
  `{"matches": [{"recipe_id", "title", "score"}], "suggestion": "..."}`

All recipe and search endpoints are strictly scoped to the authenticated
user; a user can never see or search another user's recipes.

## Verification performed

See the task report for the full pass/fail breakdown. Summary: SQLite path
fully verified (migrations, idempotent seed data, unit tests covering
embedding determinism, similarity ranking, cross-user isolation, and the
search endpoint's stub response shape) and frontend `npm run build`
verified. The Postgres + pgvector path is written correctly against the
pgvector-django API but could not be live-verified in this environment
(pgvector is not installed on the local Postgres and there is no admin
access available to install it).
