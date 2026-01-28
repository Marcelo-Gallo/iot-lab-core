import asyncio
import httpx 
import random
import logging
import sys

# --- Configurações ---
API_URL = "http://localhost:8000/api/v1"
NUM_DEVICES = 5   # Reduzi para 5 para facilitar a visualização do log
DELAY_MIN = 1.0
DELAY_MAX = 5.0

# --- Configuração de Log  ---
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SimuladorSeguro")

class DeviceBot:
    """
    Representa um dispositivo IoT simulado com Autenticação via Token.
    """
    def __init__(self, device_id: int, name: str, sensor_map: dict, token: str):
        self.device_id = device_id
        self.name = name
        self.sensor_map = sensor_map 
        self.token = token # <--- A Chave de Acesso
        self.is_running = True

    async def run(self, client: httpx.AsyncClient):
        logger.info(f"🤖 {self.name}: Boot completo. Token carregado: {self.token[:10]}...")
        
        # Headers exclusivos deste bot
        headers = {
            "x-device-token": self.token
        }
        
        while self.is_running:
            try:
                payloads = []
                
                # --- Geração de Dados ---
                if "Temperatura" in self.sensor_map:
                    temp = round(random.uniform(20.0, 35.0), 2)
                    payloads.append({
                        "device_id": self.device_id,
                        "sensor_type_id": self.sensor_map["Temperatura"],
                        "value": temp
                    })

                if "Umidade" in self.sensor_map:
                    hum = round(random.uniform(40.0, 90.0), 2)
                    payloads.append({
                        "device_id": self.device_id,
                        "sensor_type_id": self.sensor_map["Umidade"],
                        "value": hum
                    })

                # --- Envio Autenticado ---
                for p in payloads:
                    # O Header vai aqui!
                    resp = await client.post(
                        f"{API_URL}/measurements/", 
                        json=p, 
                        headers=headers 
                    )
                    
                    if resp.status_code == 200:
                        # logger.info(f"✅ {self.name}: Enviado com sucesso.")
                        pass # Silencia sucesso para não poluir, descomente se quiser ver
                    else:
                        logger.warning(f"⚠️ {self.name}: Recusado ({resp.status_code}) - {resp.text}")

                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

            except Exception as e:
                logger.error(f"❌ {self.name}: Erro de conexão - {e}")
                await asyncio.sleep(5)

async def get_admin_token(client: httpx.AsyncClient):
    """Loga como admin para poder criar devices e tokens"""
    try:
        resp = await client.post(
            f"{API_URL}/login/access-token",
            data={"username": "admin", "password": "admin123"}
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except:
        pass
    logger.critical("❌ Falha ao logar como Admin. O simulador precisa de permissão para criar Tokens.")
    sys.exit(1)

async def setup_world(client: httpx.AsyncClient):
    """
    Prepara o terreno: Cria Tipos, Devices e GERA TOKENS para cada um.
    """
    logger.info("🔐 Iniciando autenticação do Simulador...")
    admin_token = await get_admin_token(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    logger.info("🌍 Verificando Catálogo de Sensores...")
    
    # 1. Setup Sensores (Upsert)
    required_sensors = {
        "Temperatura": {"name": "Temperatura", "unit": "°C"},
        "Umidade": {"name": "Umidade", "unit": "%"}
    }
    
    try:
        r_types = await client.get(f"{API_URL}/sensor-types/")
        existing_types = {t["name"]: t["id"] for t in r_types.json()}
    except Exception as e:
        logger.critical(f"API Offline: {e}")
        sys.exit(1)

    types_map = {}
    for key, data in required_sensors.items():
        if key in existing_types:
            types_map[key] = existing_types[key]
        else:
            # Cria sensor (precisa de admin headers se tiver protegido a rota, aqui talvez nao precise, mas garante)
            r_create = await client.post(f"{API_URL}/sensor-types/", json=data, headers=admin_headers)
            if r_create.status_code == 200:
                types_map[key] = r_create.json()["id"]

    bots = []
    logger.info(f"🔨 Provisionando {NUM_DEVICES} dispositivos seguros...")
    
    for i in range(1, NUM_DEVICES + 1):
        dev_name = f"Secure Bot {i:02d}"
        dev_slug = f"secure-bot-{i:02d}"
        
        # 2. Cria/Busca Device
        # Tenta criar
        r_new = await client.post(
            f"{API_URL}/devices/", 
            json={
                "name": dev_name,
                "slug": dev_slug,
                "location": f"Simulação Zona {random.choice(['Alpha', 'Beta'])}",
                "is_active": True
            },
            headers=admin_headers
        )
        
        dev_id = None
        if r_new.status_code == 200:
            dev_id = r_new.json()["id"]
        elif r_new.status_code == 400:
            # Já existe, busca ID
            all_devs = (await client.get(f"{API_URL}/devices/", headers=admin_headers)).json()
            target = next((d for d in all_devs if d["slug"] == dev_slug), None)
            if target: dev_id = target["id"]
        
        if not dev_id: continue

        # 3. Vincula Sensores
        sensor_ids = list(types_map.values())
        await client.post(
            f"{API_URL}/devices/{dev_id}/sensors",
            json={"sensor_ids": sensor_ids},
            headers=admin_headers
        )

        # 4. GERAÇÃO DE TOKEN (A Mágica Nova)
        # Verifica se já tem token, se não, cria um novo
        # Nota: O endpoint de listagem de tokens retorna os tokens mascarados ou inteiros dependendo da sua implementação.
        # Aqui vamos assumir que criamos um novo para garantir que temos o segredo em mãos.
        
        token_secret = None
        
        # Cria um novo token específico para essa sessão de simulação
        label = f"Simulacao-{random.randint(1000,9999)}"
        r_token = await client.post(
            f"{API_URL}/devices/{dev_id}/tokens",
            json={"label": label},
            headers=admin_headers
        )
        
        if r_token.status_code == 200:
            token_secret = r_token.json()["token"]
            logger.info(f"🔑 Token gerado para {dev_name}")
        else:
            logger.error(f"❌ Erro ao gerar token: {r_token.text}")
            continue

        # Instancia o Bot com o Token
        bot = DeviceBot(dev_id, dev_name, types_map, token_secret)
        bots.append(bot)

    return bots

async def main():
    async with httpx.AsyncClient() as client:
        bots = await setup_world(client)
        
        if not bots:
            logger.error("Falha no setup. Nenhum bot operante.")
            return

        logger.info("🚀 ENXAME SEGURO INICIADO! (Ctrl+C para parar)")
        tasks = [bot.run(client) for bot in bots]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Simulação interrompida.")