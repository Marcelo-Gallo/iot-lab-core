import logging
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.sensor_type import SensorType
from app.models.organization import Organization  # <--- Novo Import

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_initial_data(session: AsyncSession) -> None:
    """
    Cria os dados base do sistema:
    1. Organização Padrão (Laboratório Principal)
    2. Usuário Admin (Vinculado à Organização)
    3. Tipos de Sensores Básicos
    """
    
    # -------------------------------------------------------------------------
    # 1. ORGANIZAÇÃO (ROOT)
    # -------------------------------------------------------------------------
    logger.info("🏢 Verificando Organização Padrão...")
    query_org = select(Organization).where(Organization.slug == "iot-lab-main")
    result_org = await session.exec(query_org)
    org = result_org.first()

    if not org:
        org = Organization(
            name="IoT Lab - Matriz",
            slug="iot-lab-main",
            description="Ambiente principal de desenvolvimento e testes."
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)
        logger.info(f"✅ Organização criada: {org.name} (ID: {org.id})")
    else:
        logger.info(f"⏭️  Organização já existe: {org.name}")

    # -------------------------------------------------------------------------
    # 2. SUPERUSER (ADMIN)
    # -------------------------------------------------------------------------
    logger.info("👤 Verificando Superusuário...")
    query_user = select(User).where(User.email == settings.FIRST_SUPERUSER)
    result_user = await session.exec(query_user)
    user = result_user.first()

    if not user:
        user = User(
            username="admin",
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_superuser=True,
            is_active=True,
            full_name="Administrador do Sistema",
            organization_id=org.id  # <--- Vinculando à Organização
        )
        session.add(user)
        await session.commit()
        logger.info(f"✅ Superusuário criado: {user.email}")
    else:
        # BACKFILL: Se o usuário já existe mas é "órfão" (sem organização), corrigimos agora.
        if not user.organization_id:
            user.organization_id = org.id
            session.add(user)
            await session.commit()
            logger.info(f"🛠️  Superusuário atualizado: Vinculado à Organização {org.id}")
        else:
            logger.info(f"⏭️  Superusuário já configurado.")

    # -------------------------------------------------------------------------
    # 3. TIPOS DE SENSORES
    # -------------------------------------------------------------------------
    logger.info("🌡️  Verificando Tipos de Sensores...")
    
    sensor_types_data = [
        {"name": "Temperatura", "unit": "°C", "code": "temp_c"},
        {"name": "Umidade Relativa", "unit": "%", "code": "hum_rel"},
        {"name": "Tensão Bateria", "unit": "V", "code": "v_bat"},
        {"name": "Luminosidade", "unit": "lux", "code": "lux"},
    ]

    for data in sensor_types_data:
        query = select(SensorType).where(SensorType.code == data["code"])
        result = await session.exec(query)
        existing = result.first()

        if not existing:
            new_type = SensorType(**data)
            session.add(new_type)
            logger.info(f"   + Criado: {data['name']}")
    
    await session.commit()
    logger.info("✅ Seed concluído com sucesso!")