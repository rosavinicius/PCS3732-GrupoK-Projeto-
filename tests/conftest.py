# Para rodar localmente: pytest tests/

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importações baseadas na estrutura do projeto
from backend.src.db.database import Base, get_db
from backend.src.api.router import api_router

# Criando um banco em memória do SQLite para testes rápidos
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configura uma mini aplicação FastAPI para injetar o router
app = FastAPI()
app.include_router(api_router)

@pytest.fixture(scope="function")
def db_session():
    """Cria uma nova sessão de banco de dados limpa para um teste."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Substitui a dependência do banco pela versão de teste."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)