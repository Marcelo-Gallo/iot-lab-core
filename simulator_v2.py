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
    Prepara o terreno: descobre tipos de sensores e cria/recupera devices.
    """
    logger.info("🌍 Inicializando a Matrix (Setup)...")
    
    # Buscar Tipos de Sensores
    try:
        r_types = await client.get(f"{API_URL}/sensor-types/")
        r_types.raise_for_status()
        types_list = r_types.json()
        # Cria mapa: Nome -> ID
        types_map = {t["name"]: t["id"] for t in types_list}
        logger.info(f"📋 Tipos de Sensores Encontrados: {types_map}")
    except Exception as e:
        logger.critical(f"Falha ao buscar tipos de sensores. O servidor está rodando? Erro: {e}")
        sys.exit(1)

    bots = []
    
    # Criar/Recuperar Dispositivos
    logger.info(f"🔨 Fabricando {NUM_DEVICES} dispositivos virtuais...")
    
    for i in range(1, NUM_DEVICES + 1):
        dev_name = f"Bot Device {i:02d}"
        dev_slug = f"bot-device-{i:02d}"
        
        payload = {
            "name": dev_name,
            "slug": dev_slug,
            "location": f"Simulação Zona {random.choice(['A', 'B', 'C'])}",
            "is_active": True
        }

        # Tenta criar
        r_new = await client.post(f"{API_URL}/devices/", json=payload)
        
        if r_new.status_code == 200:
            # Sucesso: Criou novo
            data = r_new.json()
            dev_id = data["id"]
            logger.info(f"✨ Criado: {dev_name} (ID: {dev_id})")
        
        elif r_new.status_code == 400:
            # Erro 400 geralmente é "Slug já existe". Vamos buscar o ID dele.
            # Nota: Numa API real, teríamos um GET /devices/{slug}, mas vamos listar todos.
            # Otimização simples: listar todos uma vez fora do loop seria melhor, 
            # mas para setup inicial isso serve.
            all_devs = (await client.get(f"{API_URL}/devices/?limit=1000")).json()
            target = next((d for d in all_devs if d["slug"] == dev_slug), None)
            
            if target:
                dev_id = target["id"]
            else:
                logger.error(f"💀 Erro: Device {dev_slug} existe mas não foi encontrado na lista.")
                continue
        else:
            logger.error(f"💀 Erro desconhecido ao criar device: {r_new.text}")
            continue

        # Instancia o Bot
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