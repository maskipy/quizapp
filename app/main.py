"""
QuizApp API — entrypoint.

"""

from fastapi import FastAPI

app = FastAPI(
    title="QuizApp API",
    description="Real-time quiz and flashcard platform for algorithm learning.",
    version="0.1.0",
)


@app.get("/")
def root():
    return "Hello Lord"


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
