# QuizApp

A flashcard and quiz platform for algorithm learning, built for my CPGE students. Teachers create decks and classes, choose exactly which decks to share with which class, and students study them in a flip-card interface.

## Status

Working locally: accounts, decks and cards, classes with join codes, read-only deck sharing, and a study mode. Not deployed yet. Automated tests are in progress.

## Features

- **Accounts:** JWT-based authentication, with two roles: student and teacher.
- **Decks and cards:** full create / read / update / delete, paginated lists. Each user sees only their own.
- **Classes:** a teacher creates a class and gets a short join code; students join with it.
- **Sharing:** a teacher picks which decks to share with which class. Students can study shared decks read-only and can never change them.
- **Study mode:** flip-card review with progress and keyboard shortcuts.
- **Frontend:** plain HTML/CSS/JS, mobile-friendly, served by the API itself (one process, no CORS).

## Stack

| | |
|---|---|
| API | FastAPI, fully async |
| Database | PostgreSQL 18 via SQLModel (SQLAlchemy 2.0 async) and psycopg 3 |
| Migrations | Alembic |
| Auth | JWT (PyJWT), Argon2id password hashing (pwdlib) |
| Tooling | uv, Ruff, GitHub Actions (lint and format checks), Docker Compose (local Postgres) |
| Frontend | Vanilla HTML / CSS / JavaScript |

Planned, not built yet: Redis (rate limiting), a pytest suite running in CI, and a Docker image of the app itself.

## Getting started

Requires Docker and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/maskipy/quizapp.git
cd quizapp
docker compose up -d           # starts Postgres on localhost:5430
cp .env.example .env           # then set SECRET_KEY (below)
uv sync
uv run alembic upgrade head    # creates the schema
uv run fastapi dev app/main.py
```

Generate a `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Open `http://127.0.0.1:8000`. Interactive API docs are at `/docs`.

### Creating a teacher

Everyone registers as a student. There is no admin UI on purpose: promoting someone to teacher is done from the command line.

```bash
uv run python -m app.cli set-role you@example.com teacher
```

The change takes effect immediately, with no re-login.

## API overview

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register` · `POST /auth/login` · `GET /auth/me` |
| Decks | `POST /decks` · `GET /decks` · `GET/PATCH/DELETE /decks/{id}` · `GET /decks/{id}/classes` |
| Cards | `POST/GET /decks/{id}/cards` · `PATCH/DELETE /decks/{id}/cards/{card_id}` |
| Classes | `POST /classes` · `GET /classes` · `POST /classes/join` · `GET/DELETE /classes/{id}` · `POST /classes/{id}/leave` |
| Members | `GET /classes/{id}/members` · `DELETE /classes/{id}/members/{user_id}` |
| Sharing | `GET /classes/{id}/decks` · `PUT/DELETE /classes/{id}/decks/{deck_id}` |

Full request and response schemas are in the interactive docs.

## Project structure

```
app/
  main.py        app assembly (routers + static files)
  cli.py         admin commands (set a user's role)
  core/          configuration, security (hashing, JWT)
  db/            async engine and session
  models/        SQLModel tables and request/response schemas
  api/           dependencies (auth, ownership) and routes
migrations/      Alembic migrations
static/          frontend (HTML / CSS / JS)
tests/           tests (in progress)
```

## Checks

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

## Roadmap

**Built:** authentication and roles · decks and cards · classes and join codes · read-only deck sharing · study mode · migrations · CI (lint and format)

**In progress:** automated tests (unit tests first, then database-backed tests, then CI)

**Planned:** recording study activity ("knew it / missed it") · teacher progress dashboard · timed exams · login rate limiting (Redis) · refresh tokens · Docker image and deployment

## License

MIT