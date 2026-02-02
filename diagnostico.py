import asyncio
from sqlmodel import select
from app.core.database import get_session
from app.models.device import Device
from app.models.sensor_type import SensorType
from app.models.device_sensor import DeviceSensorLink
from app.models.device_token import DeviceToken
import secrets

async def diagnostico_calibracao():
    print("\n🕵️‍♂️ INICIANDO DIAGNÓSTICO DE CALIBRAÇÃO...\n")
    async_gen = get_session()
    session = await anext(async_gen)

    # 1. Garantir Device e Sensor
    dev = await session.get(Device, 1)
    if not dev:
        print("⚠️ Device 1 não encontrado. Criando...")
        dev = Device(id=1, name="Dispositivo de Teste", location="Lab Debug", is_active=True)
        session.add(dev)
    
    sensor = await session.get(SensorType, 1)
    if not sensor:
        print("⚠️ Sensor 1 não encontrado. Criando...")
        sensor = SensorType(id=1, name="Sensor Genérico", unit="un", is_active=True)
        session.add(sensor)
    
    await session.commit()

    # 2. Configurar a Fórmula
    link = await session.get(DeviceSensorLink, (1, 1))
    if not link:
        print("⚠️ Vínculo não encontrado. Criando...")
        link = DeviceSensorLink(device_id=1, sensor_type_id=1)
    
    print(f"🔧 Aplicando fórmula 'x / 2' no Device 1 + Sensor 1...")
    link.calibration_formula = "x / 2"
    session.add(link)
    
    # 3. Gerar/Pegar Token
    query_token = select(DeviceToken).where(DeviceToken.device_id == 1)
    result = await session.exec(query_token)
    token_obj = result.first()
    
    if not token_obj:
        print("🔑 Gerando novo token...")
        token_str = secrets.token_hex(32)
        token_obj = DeviceToken(device_id=1, token=token_str)
        session.add(token_obj)
    
    await session.commit()
    
    print("\n✅ AMBIENTE PRONTO!")
    print("="*60)
    print(f"📍 Device ID: 1")
    print(f"📍 Sensor ID: 1")
    print(f"⚗️  Fórmula : {link.calibration_formula}")
    print(f"🔑 Token   : {token_obj.token}")
    print("="*60)
    
    # Monta o comando CURL para o usuário
    cmd = (
        f"curl -X 'POST' 'http://localhost:8000/api/v1/measurements/' "
        f"-H 'Content-Type: application/json' "
        f"-H 'x-device-token: {token_obj.token}' "
        f"-d '{{\"device_id\": 1, \"sensor_type_id\": 1, \"value\": 100}}'"
    )
    print("\n📋 COPIE E RODE O COMANDO ABAIXO EM OUTRO TERMINAL:\n")
    print(cmd)
    print("\n" + "="*60)

    await session.close()

if __name__ == "__main__":
    asyncio.run(diagnostico_calibracao())