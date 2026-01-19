from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.api import api_router
from app.core.database import init_db

# --- IMPORTS DE MODELOS ---
# Importamos todos para garantir que o SQLModel detecte os metadados
from app.models.device import Device
from app.models.sensor_type import SensorType
from app.models.measurement import Measurement
from app.models.device_sensor import DeviceSensorLink # <--- ADICIONE ESTA LINHA

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Cria as tabelas no banco de forma assíncrona
    await init_db()
    print("✅ Tabelas verificadas/criadas (Async).")
    
    yield # A aplicação roda aqui
    
    print("🛑 Encerrando aplicação.")

# --- APP SETUP ---
app = FastAPI(
    title="IoT Lab Core", 
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"status": "ok", "mensagem": "Sistema operando em normalidade"}

app.include_router(api_router, prefix="/api/v1")