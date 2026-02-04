import asyncio
import httpx
import random
import logging

# CONFIGURAÇÃO DO TESTE
# Cole aqui os tokens que você gerou no Dashboard
TOKEN_ORG_A = "sk_iot_nlmp2RpGPnKWtHk7khrv1dfPikQf3jRBLzbRHRS_VYo"
TOKEN_ORG_B = "sk_iot_RdExDdqMzi7iTwXebuW6UX0GVk7yI7E7EON1QgvFVD4"

API_URL = "http://localhost:8000/api/v1/measurements/"

# Configuração de Log
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VirtualDevice")

async def simulate_device(name: str, token: str, sensor_id: int, interval: float):
    """
    Simula um loop infinito de envio de dados de sensor.
    """
    async with httpx.AsyncClient() as client:
        logger.info(f"🚀 [{name}] Iniciando simulação...")
        
        while True:
            # Gera valor aleatório (Temperatura simulada)
            value = round(random.uniform(20.0, 35.0), 2)
            
            payload = {
                "sensor_type_id": sensor_id, # Assumindo 1 = Temperatura (do Seed)
                "value": value,
                "timestamp": None
            }
            
            try:
                response = await client.post(
                    API_URL, 
                    json=payload, 
                    headers={"X-Device-Token": token}
                )
                
                if response.status_code == 200:
                    logger.info(f"📡 [{name}] Enviado: {value}°C | Status: 200 OK")
                else:
                    logger.warning(f"⚠️ [{name}] Falha: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"❌ [{name}] Erro de Conexão: {e}")
            
            await asyncio.sleep(interval)

async def main():
    if "COLE_O_TOKEN" in TOKEN_ORG_A or "COLE_O_TOKEN" in TOKEN_ORG_B:
        logger.error("⛔ PARE! Você precisa colar os tokens reais no arquivo antes de rodar.")
        return

    logger.info("⚔️  INICIANDO TESTE DE ISOLAMENTO DE TENANTS ⚔️")
    
    # Roda os dois dispositivos em paralelo (Concorrência Real)
    await asyncio.gather(
        simulate_device("DEVICE_SPACEX", TOKEN_ORG_A, sensor_id=1, interval=2.0),
        simulate_device("DEVICE_BLUE",   TOKEN_ORG_B, sensor_id=1, interval=2.0)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Simulação encerrada.")