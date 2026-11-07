# Money Tracker

A personal finance app: track income and expenses by category, see your balance and monthly
spending, and get budgeting advice from an AI assistant powered by Google Gemini.
Backend in FastAPI and PostgreSQL, with a single-page frontend served by the API.

## Features

- **Authentication:** registration and login with bcrypt-hashed passwords and expiring JWT tokens
- **Data isolation:** every query is scoped to the logged-in user; other users' data is never visible
- **Transactions:** create, list, update and delete income and expense records
- **Filtering and pagination:** by category, type (income or expense) and date range, newest first
- **Categories:** each user manages their own expense categories
- **Exact money values:** amounts are `Decimal` in Python and `NUMERIC(12, 2)` in PostgreSQL, never floats, and are returned as strings in JSON (`"19.99"`) so no precision is lost
- **Statistics:** current balance, total income and expenses, and spending per category for the current month
- **AI advisor:** sends the month's spending summary to Gemini and returns a short analysis with saving tips, or answers the user's own question about their spending

## Tech stack

| Part | Technology |
| --- | --- |
| Backend | FastAPI |
| Database | PostgreSQL 15, SQLAlchemy |
| Migrations | Alembic |
| Authentication | JWT (python-jose), bcrypt (passlib) |
| AI | Google Gemini API (google-genai) |
| Containers | Docker, Docker Compose |
| Frontend | Single `index.html` page |
| Dependencies | Poetry |

## Running with Docker

```bash
cp .env.example .env       # fill in the values; SECRET_KEY e.g. from: openssl rand -hex 32
docker compose up -d --build
```

The web container waits for PostgreSQL to be healthy and applies the Alembic migrations on startup.

- App: http://127.0.0.1:8000
- API documentation (Swagger): http://127.0.0.1:8000/docs
- The database is reachable from your machine on port `5433`.

`GEMINI_API_KEY` is only needed for the AI advisor; everything else works without it.
The Docker setup is meant for development (code is mounted into the container and reloads on change).

## API

| Method | Path | Description |
| --- | --- | --- |
| POST | `/auth/register` | Register |
| POST | `/auth/login` | Log in (form data), returns a JWT |
| GET | `/users/me` | Your profile |
| GET | `/users/me/balance` | Balance, total income and total expenses |
| POST | `/transactions` | Add an income or expense |
| GET | `/transactions` | List transactions; filters: `category_id`, `type`, `date_from`, `date_to`, `limit`, `offset` |
| PATCH | `/transactions/{id}` | Update a transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |
| POST | `/categories` | Create an expense category |
| GET | `/categories` | Your categories |
| GET | `/statistics/monthly` | Spending per category this month, largest first |
| POST | `/ai/chat` | AI analysis of this month's spending; optional body `{"prompt": "..."}` to ask a question (needs `GEMINI_API_KEY`) |
| GET | `/health` | Health check |

All endpoints except register, login and health require a JWT (`Authorization: Bearer <token>`).

## Project structure

```
app/
  main.py          app setup and routers
  routers/         one file per feature: auth, users, transactions, categories, statistics, ai
  repository.py    SQLAlchemy models and database queries
  schemas.py       Pydantic request/response schemas
  security.py      password hashing and JWT handling
  database.py      database engine and session
alembic/           database migrations
static/index.html  frontend
```
