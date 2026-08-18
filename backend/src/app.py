import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI

from api.router import api_router

app = FastAPI(
    title="Irrigador API",
    description="REST API para o backend do sistema de irrigação.",
    version="1.0.0",
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
