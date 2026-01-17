import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session

# Cria Engine em Memória (SQLite)
engine_test = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

# Fixture da Sessão
# Executa antes de cada teste
@pytest.fixture(name="session")
def session_fixture():
    # Cria as tabelas vazias
    SQLModel.metadata.create_all(engine_test)
    
    with Session(engine_test) as session:
        yield session  # Entrega a sessão para o teste usar
    
    # Limpa tudo depois do teste
    SQLModel.metadata.drop_all(engine_test)

# Fixture do Cliente
@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    
    client = TestClient(app)
    yield client
    
    # Limpa a sobrescrita depois
    app.dependency_overrides.clear()