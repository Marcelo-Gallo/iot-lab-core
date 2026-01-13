from sqlmodel import Session, select
from app.models.sensor_type import SensorType
from app.models.device import Device

def create_initial_data(session: Session):
    """
    Verifica se os tipos básicos de sensores existem.
    Se não, cria eles.
    """
    # Lista do que é é necessário que exista no banco
    initial_types = [
        {"name": "Temperatura", "unit": "°C", "description": "Temperatura Ambiente"},
        {"name": "Umidade", "unit": "%", "description": "Umidade Relativa do Ar"},
    ]

    for data in initial_types:
        # Verifica se já existe pelo nome
        query = select(SensorType).where(SensorType.name == data["name"])
        existing = session.exec(query).first()

        # Se não existir, cria
        if not existing:
            print(f"🌱 Semeando banco: Criando sensor '{data['name']}'...")
            sensor_type = SensorType(**data) # Desempacota o dicionário
            session.add(sensor_type)

    #Lista de Dispositivos
    initial_devices = [
        {
            "name": "Protótipo ESP32 - Alpha",
            "slug": "esp32-alpha",
            "location": "Laboratório 1",
            "is_active": True
        },
        {
            "name": "Estação Meteorológica",
            "slug": "weather-station-01",
            "location": "Telhado",
            "is_active": True
        }
    ]

    for dev_data in initial_devices:
        # Verifica pelo SLUG (que é único)
        query = select(Device).where(Device.slug == dev_data["slug"])
        existing = session.exec(query).first()

        if not existing:
            print(f"🌱 Seed: Criando Dispositivo '{dev_data['name']}'...")
            device = Device(**dev_data)
            session.add(device)
    
    # Salva tudo
    session.commit()