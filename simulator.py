import time
import random
import requests

# Configurações
API_URL = "http://localhost:8000/api/v1"
DEVICE_ID = 1  # <--- Vamos fingir que somos o device com ID 1
DELAY = 2      # Segundos entre envios

def get_sensor_types():
    """Busca os IDs dos tipos de sensor para garantir que existem"""
    try:
        response = requests.get(f"{API_URL}/sensor-types/")
        return {item['name']: item['id'] for item in response.json()}
    except Exception as e:
        print(f"❌ Erro ao buscar tipos de sensor: {e}")
        return {}

def simular():
    print(f"🚀 Iniciando simulação para o Dispositivo {DEVICE_ID}...")
    
    # 1. Descobre os IDs do banco (Temperatura e Umidade)
    types = get_sensor_types()
    if not types:
        print("⚠️  Nenhum tipo de sensor encontrado. O banco está vazio?")
        return

    print(f"📋 Tipos detectados: {types}")
    print("📡 Enviando dados... (Pressione Ctrl+C para parar)")

    while True:
        # 2. Gera dados aleatórios (com flutuação realista)
        # Temperatura entre 22.0 e 28.0
        temp_val = round(random.uniform(22.0, 28.0), 2)
        # Umidade entre 50.0 e 60.0
        hum_val = round(random.uniform(50.0, 60.0), 2)

        # 3. Prepara os pacotes
        payloads = [
            {
                "device_id": DEVICE_ID,
                "sensor_type_id": types.get("Temperatura", 1), # Tenta pegar o ID correto
                "value": temp_val
            },
            {
                "device_id": DEVICE_ID,
                "sensor_type_id": types.get("Umidade", 2),
                "value": hum_val
            }
        ]

        # 4. Envia para a API
        for data in payloads:
            try:
                res = requests.post(f"{API_URL}/measurements/", json=data)
                if res.status_code == 200:
                    print(f"✅ Enviado: {data['value']} | ID: {res.json()['id']}")
                else:
                    print(f"❌ Erro {res.status_code}: {res.text}")
            except Exception as e:
                print(f"⚠️  API Offline? {e}")

        # Aguarda
        time.sleep(DELAY)

if __name__ == "__main__":
    simular()