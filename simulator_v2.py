import asyncio
import httpx 
import random
import logging
import sys

# --- Configurações ---
API_URL = "http://localhost:8000/api/v1"
NUM_DEVICES = 10  # Quantidade de "robôs"
DELAY_MIN = 1.0   # Tempo mínimo entre envios (segundos)
DELAY_MAX = 5.0   # Tempo máximo entre envios (segundos)

# --- Configuração de Log  ---
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SwarmSimulator")

class DeviceBot:
    """
    Representa um dispositivo IoT simulado.
    Cada instância roda de forma independente (concorrente).
    """
    def __init__(self, device_id: int, name: str, sensor_map: dict):
        self.device_id = device_id
        self.name = name
        self.sensor_map = sensor_map # Ex: {'Temperatura': 1, 'Umidade': 2}
        self.is_running = True

    async def run(self, client: httpx.AsyncClient):
        logger.info(f"🤖 {self.name}: Online e operando. ID={self.device_id}")
        
        while self.is_running:
            try:
                payloads = []
                
                # --- Lógica de Geração de Dados ---
                # Temperatura: Faixa 20°C - 35°C
                if "Temperatura" in self.sensor_map:
                    # Adiciona uma flutuação aleatória mas "suave" seria o ideal. 
                    # Por enquanto, random puro.
                    temp = round(random.uniform(20.0, 35.0), 2)
                    payloads.append({
                        "device_id": self.device_id,
                        "sensor_type_id": self.sensor_map["Temperatura"],
                        "value": temp
                    })

                # Umidade: Faixa 40% - 90%
                if "Umidade" in self.sensor_map:
                    hum = round(random.uniform(40.0, 90.0), 2)
                    payloads.append({
                        "device_id": self.device_id,
                        "sensor_type_id": self.sensor_map["Umidade"],
                        "value": hum
                    })

                # --- Envio em Batch (Sequencial por Bot) ---
                for p in payloads:
                    resp = await client.post(f"{API_URL}/measurements/", json=p)
                    
                    if resp.status_code != 200:
                        logger.warning(f"⚠️ {self.name}: Falha ao enviar dado. {resp.text}")

                # Pausa aleatória para simular assincronicidade real da rede -> Sugestão Gemini
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

            except Exception as e:
                logger.error(f"❌ {self.name}: Erro crítico - {e}")
                # Espera um pouco mais se der erro para não floodar logs
                await asyncio.sleep(5)

async def setup_world(client: httpx.AsyncClient):
    """
    Prepara o terreno: Garante que existem Tipos de Sensores e Dispositivos.
    """
    logger.info("🌍 Inicializando a Matrix (Setup)...")
    
    # --- 1. GARANTIR TIPOS DE SENSORES (SELF-SEEDING) ---
    # Define o que o simulador PRECISA para funcionar
    required_sensors = {
        "Temperatura": {"name": "Temperatura", "unit": "°C"},
        "Umidade": {"name": "Umidade", "unit": "%"}
    }
    
    # Busca o que já tem no banco
    try:
        r_types = await client.get(f"{API_URL}/sensor-types/")
        existing_types = {t["name"]: t["id"] for t in r_types.json()}
    except Exception as e:
        logger.critical(f"Erro ao conectar na API: {e}")
        sys.exit(1)

    types_map = {}
    
    # Lógica de "Upsert" (Se não existe, cria)
    for key, data in required_sensors.items():
        if key in existing_types:
            types_map[key] = existing_types[key]
            # logger.info(f"✅ Tipo encontrado: {key}")
        else:
            # Cria se não existir
            logger.info(f"🌱 Criando tipo de sensor ausente: {key}...")
            r_create = await client.post(f"{API_URL}/sensor-types/", json=data)
            if r_create.status_code == 200:
                new_id = r_create.json()["id"]
                types_map[key] = new_id
                logger.info(f"✨ Tipo criado: {key} (ID: {new_id})")
            else:
                logger.error(f"❌ Falha ao criar sensor {key}: {r_create.text}")

    logger.info(f"📋 Mapa de Sensores: {types_map}")

    # --- 2. CRIAR DISPOSITIVOS (Igual ao anterior) ---
    bots = []
    logger.info(f"🔨 Fabricando {NUM_DEVICES} dispositivos virtuais...")
    
    # ... (O resto do código de devices permanece idêntico, pode manter) ...
    # Vou repetir o bloco for de devices para facilitar o copy-paste seguro
    
    for i in range(1, NUM_DEVICES + 1):
        dev_name = f"Bot Device {i:02d}"
        dev_slug = f"bot-device-{i:02d}"
        
        payload = {
            "name": dev_name,
            "slug": dev_slug,
            "location": f"Simulação Zona {random.choice(['A', 'B', 'C'])}",
            "is_active": True
        }

        r_new = await client.post(f"{API_URL}/devices/", json=payload)
        
        if r_new.status_code == 200:
            dev_id = r_new.json()["id"]
            logger.info(f"✨ {dev_name} criado com sucesso.")
        elif r_new.status_code == 400:
            # Busca ID se já existe
            all_devs = (await client.get(f"{API_URL}/devices/?limit=1000")).json()
            target = next((d for d in all_devs if d["slug"] == dev_slug), None)
            if target: 
                dev_id = target["id"]
                # logger.info(f"ℹ️ {dev_name} já existe (ID: {dev_id}).")
            else: continue
        else:
            logger.error(f"❌ Falha ao criar {dev_name}: {r_new.text}")
            continue

        # --- NOVA PARTE: O PROVISIONAMENTO AUTOMÁTICO (FASE 9) ---
        # Agora o simulador avisa a API: "Ei, esse robô TEM esses sensores!"
        sensor_ids_to_link = list(types_map.values()) # Pega IDs de Temp e Umid
        
        r_link = await client.post(
            f"{API_URL}/devices/{dev_id}/sensors",
            json={"sensor_ids": sensor_ids_to_link}
        )
        
        if r_link.status_code == 200:
            logger.info(f"🔗 Sensores vinculados ao {dev_name}: {list(types_map.keys())}")
        else:
            logger.warning(f"⚠️ Falha ao vincular sensores no {dev_name}: {r_link.text}")
        # ---------------------------------------------------------

        bot = DeviceBot(dev_id, dev_name, types_map)
        bots.append(bot)

    return bots

async def main():
    async with httpx.AsyncClient() as client:
        # Configura o cenário
        bots = await setup_world(client)
        
        if not bots:
            logger.error("Nenhum bot foi criado. Abortando.")
            return

        logger.info("🚀 Lançando o ENXAME! Pressione Ctrl+C para parar.")
        
        # Inicia todos os loops concorrentes
        tasks = [bot.run(client) for bot in bots]
        
        # O gather roda tudo junto
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Simulação interrompida pelo usuário.")