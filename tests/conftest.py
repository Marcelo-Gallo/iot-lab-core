import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session

# Configura Banco em Memória Assíncrono (SQLite + aiosqlite)
# StaticPool garante que a conexão persista na memória entre requisições
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

# Fixture da Sessão do Banco
@pytest_asyncio.fixture
async def session():
    # Cria as tabelas
    async with engine_test.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Cria a sessão
    async_session = sessionmaker(
        engine_test, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        
    # Limpa as tabelas (Drop)
    async with engine_test.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

# Fixture do Cliente HTTP Assíncrono
@pytest_asyncio.fixture
async def async_client(session: AsyncSession):
    # Dependency Override: Faz a API usar nosso banco de teste
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    
    # Cria o cliente apontando para a app FastAPI
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()