from fastapi import APIRouter
from app.api.v1.endpoints import devices, sensor_types, measurements, login, organizations, users, onboarding

api_router = APIRouter()

api_router.include_router(login.router, tags=["Login"])

# Inclui as rotas de devices com o prefixo /devices
api_router.include_router(devices.router, prefix="/devices", tags=["Dispositivos"])
api_router.include_router(sensor_types.router, prefix="/sensor-types", tags=["Tipos de Sensor"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["Medições (Dados)"])

api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizações"])

api_router.include_router(users.router, prefix="/users", tags=["Usuários"])

api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding (Setup)"])