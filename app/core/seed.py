from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession # <--- Import Async

from app.models.sensor_type import SensorType
from app.models.device import Device
from app.models.user import User
from app.core.security import get_password_hash

async def create_initial_data(session: AsyncSession): # <--- Função agora é async
    initial_types = [
        {"name": "Temperatura", "unit": "°C", "description": "Temperatura Ambiente"},
        {"name": "Umidade", "unit": "%", "description": "Umidade Relativa do Ar"},
    ]
    
    for data in initial_types:
        result = await session.exec(select(SensorType).where(SensorType.name == data["name"]))
        if not result.first():
            print(f"🌱 Seed: Criando sensor '{data['name']}'...")
            session.add(SensorType(**data))

    result = await session.exec(select(User).where(User.username == "admin"))
    if not result.first():
        print("👤 Seed: Criando Superusuário 'admin'...")
        user = User(
            username="admin",
            email="admin@iotlab.com",
            hashed_password=get_password_hash("admin123"),
            is_superuser=True,
            is_active=True,
        )
        session.add(user)
    
    await session.commit()