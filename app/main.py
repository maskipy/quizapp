"""
QuizApp API — entrypoint.

"""

from fastapi import FastAPI

from app.api.routes import auth, cards, decks

app = FastAPI(
    title="QuizApp API",
    description="Real-time quiz and flashcard platform for algorithm learning.",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(decks.router)
app.include_router(cards.router)


@app.get("/")
def root():
    return "Hello Lord"


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
