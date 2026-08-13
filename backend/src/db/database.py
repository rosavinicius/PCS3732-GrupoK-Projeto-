from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ============================================================
# Caminho do banco SQLite
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "irrigation.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ============================================================
# Engine
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessário para SQLite + FastAPI
    echo=False,                                 # True para visualizar o SQL no terminal
)


# ============================================================
# Session Factory
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ============================================================
# Base para os modelos
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# Importa os modelos para registrar as tabelas no metadata
# ============================================================
from . import models  # noqa: E402,F401


# ============================================================
# Garante que as tabelas sejam criadas automaticamente
# ============================================================
Base.metadata.create_all(bind=engine)


# ============================================================
# Dependency para FastAPI
# ============================================================

def get_db():
    """
    Cria uma sessão com o banco e garante seu fechamento ao
    final da requisição.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()