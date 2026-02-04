import logging
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.sensor_type import SensorType
from app.models.organization import Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_initial_data(session: AsyncSession) -> None:
    """
    Seed Idempotente: Garante que o estado base do sistema esteja correto.
    Força atualização de senha do Superuser se estiver divergente.
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
        logger.info(f"✅ Organização criada: {org.name}")
    else:
        logger.info(f"⏭️  Organização já existe: {org.name}")

    # -------------------------------------------------------------------------
    # 2. SUPERUSER (ADMIN)
    # -------------------------------------------------------------------------
    # ATENÇÃO: O Login usa EMAIL, então o seed deve garantir esse email.
    logger.info("👤 Verificando Superusuário...")
    query_user = select(User).where(User.email == settings.FIRST_SUPERUSER)
    result_user = await session.exec(query_user)
    user = result_user.first()

    # Prepara o hash da senha atual do .env
    new_password_hash = get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)

    if not user:
        # Criação
        user = User(
            username="admin", # Username interno (pode ser usado para display)
            email=settings.FIRST_SUPERUSER, # Chave de Login
            hashed_password=new_password_hash,
            is_superuser=True,
            is_active=True,
            full_name="Administrador do Sistema",
            organization_id=org.id
        )
        session.add(user)
        await session.commit()
        logger.info(f"✅ Superusuário criado: {user.email}")
    else:
        # ATUALIZAÇÃO FORÇADA (Self-Healing)
        # Se a senha mudou ou ele está órfão, corrigimos agora.
        changes = False
        
        if not user.organization_id:
            user.organization_id = org.id
            changes = True
            logger.info("🛠️  Corrigindo: Vinculando admin à organização.")

        if not user.is_superuser:
            user.is_superuser = True
            changes = True
            logger.info("🛠️  Corrigindo: Promovendo a Superuser.")
            
        # Opcional: Sempre reseta a senha para garantir acesso
        # (Ideal para dev, cuidado em prod)
        user.hashed_password = new_password_hash
        changes = True
        
        if changes:
            session.add(user)
            await session.commit()
            logger.info(f"🔄 Superusuário atualizado com as credenciais do .env")
        else:
            logger.info(f"⏭️  Superusuário íntegro.")

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
        if not result.first():
            new_type = SensorType(**data)
            session.add(new_type)
            logger.info(f"   + Criado: {data['name']}")
    
    await session.commit()
    logger.info("✅ Seed concluído!")