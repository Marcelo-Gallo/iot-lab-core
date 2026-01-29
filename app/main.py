from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.api import api_router
from app.core.database import init_db
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import init_db, engine
from app.core.seed import create_initial_data

# --- IMPORTS DE MODELOS ---
from app.models.device import Device
from app.models.sensor_type import SensorType
from app.models.measurement import Measurement
from app.models.device_sensor import DeviceSensorLink
from app.models.device_token import DeviceToken

# --- IMPORT DO MIDDLEWARE ---
from app.core.middleware import DeviceAuthMiddleware     

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Cria as tabelas no banco de forma assíncrona
    await init_db()
    print("✅ Tabelas verificadas/criadas (Async).")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await create_initial_data(session)
        print("✅ Seed executado com sucesso.")

    yield # A aplicação roda aqui
    
    print("🛑 Encerrando aplicação.")

# --- APP SETUP ---
app = FastAPI(
    title="IoT Lab Core", 
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(DeviceAuthMiddleware)

@app.get("/")
async def root():
    return {"status": "ok", "mensagem": "Sistema operando em normalidade"}

app.include_router(api_router, prefix="/api/v1")