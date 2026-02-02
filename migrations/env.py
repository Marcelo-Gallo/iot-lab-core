import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context

# 1. Importar a Configuração do Projeto
from app.core.config import settings

# 2. Importar TODOS os modelos para que o Alembic "enxergue" as tabelas.
from app.models.device import Device
from app.models.sensor_type import SensorType
from app.models.measurement import Measurement
from app.models.user import User
from app.models.device_sensor import DeviceSensorLink
from app.models.device_token import DeviceToken  # Novo modelo de Tokens

# --- Configuração Padrão do Alembic ---
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define o alvo para o 'autogenerate'
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline'."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Função síncrona que executa a migração de fato."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Executa migrações no modo 'online'."""
    
    # 1. Ler a URL da configuração
    db_url = settings.DATABASE_URL

    # 2. HACK: Forçar o driver asyncpg se a URL vier como padrão postgresql://
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    configuration = config.get_section(config.config_ini_section)
    
    # 3. Injetar a URL corrigida na configuração do Alembic
    configuration["sqlalchemy.url"] = db_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Aqui ele chama a função síncrona dentro do contexto async
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())