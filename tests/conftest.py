import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session

# 1. Cria Engine em Memória (SQLite)
# StaticPool: Garante que a mesma conexão seja usada (essencial para testes em memória)
engine_test = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

# 2. Fixture da Sessão
# Executa ANTES de cada teste
@pytest.fixture(name="session")
def session_fixture():
    # Cria as tabelas vazias
    SQLModel.metadata.create_all(engine_test)
    
    with Session(engine_test) as session:
        yield session  # Entrega a sessão para o teste usar
    
    # Limpa tudo DEPOIS do teste
    SQLModel.metadata.drop_all(engine_test)

# 3. Fixture do Cliente (O "Navegador" do teste)
@pytest.fixture(name="client")
def client_fixture(session: Session):
    # A MÁGICA: Engana o FastAPI. 
    # Quando ele pedir "get_session", entregamos nossa sessão de teste em memória.
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    
    client = TestClient(app)
    yield client
    
    # Limpa a sobrescrita depois
    app.dependency_overrides.clear()