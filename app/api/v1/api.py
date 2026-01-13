from fastapi import APIRouter
from app.api.v1.endpoints import devices, sensor_types, measurements

api_router = APIRouter()
# Inclui as rotas de devices com o prefixo /devices
api_router.include_router(devices.router, prefix="/devices", tags=["Dispositivos"])

api_router.include_router(sensor_types.router, prefix="/sensor-types", tags=["Tipos de Sensor"])

api_router.include_router(measurements.router, prefix="/measurements", tags=["Medições (Dados)"])