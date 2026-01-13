from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session
from app.core.config import settings


from app.models.device import Device #Garante que o SQLModel leia a classe
from app.models.sensor_type import SensorType
from app.models.measurement import Measurement

from app.core.database import create_db_and_tables, engine
from app.core.seed import create_initial_data

from app.api.v1.api import api_router #Roteador Principal


@asynccontextmanager
async def lifespan(app: FastAPI):
	#Antes do app iniciar:
	print("Start: Criar tabelas no Bando de Dados")
	create_db_and_tables()

	with Session(engine) as session:
		create_initial_data(session)

	yield


	#Depois do app desligar
	print("Shutdown: Desligando")
	
app = FastAPI(
	title=settings.PROJECT_NAME,
	version="0.1.0",
	lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1") # Refistra as rotas da V1

@app.get("/")
def health_check():
	return {"status": "ok", "mensagem": "Sistema operando em normalidade"}