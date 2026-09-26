# QuizApp

A flashcard and quiz platform for practicing algorithms and data structures — built for my CPGE students

## Status

MVP complete — the full loop works end to end.

- JWT-based auth (register, login, protected routes)
- Deck and card management, scoped per user, with pagination
- A study mode with a flip-card review flow
- Fully async backend (FastAPI + PostgreSQL 18), schema versioned with Alembic

## Stack

FastAPI · PostgreSQL (SQLModel + psycopg 3) · Alembic · JWT (PyJWT) + Argon2 (pwdlib) · Ruff · uv · vanilla HTML/CSS/JS frontend 

## Running it locally

Requires Docker and [uv](https://docs.astral.sh/uv/).

```bash
docker compose up -d
cp .env.example .env   # then set SECRET_KEY -- see below
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Generate a `SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Open `http://127.0.0.1:8000`. Interactive API docs at `/docs`.

## Not built yet

No automated tests, no rate limiting/leaderboard, no refresh tokens, not deployed.
