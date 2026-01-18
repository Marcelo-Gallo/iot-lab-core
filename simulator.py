import time
import random
import requests

API_URL = "http://localhost:8000/api/v1"

# --- DEFINIÇÃO DO CAMPUS ---
# Nomes reais que aparecerão no Dashboard
CENARIOS = [
    {
        "name": "Estufa Botânica",
        "slug": "estufa-botanica",
        "location": "Bloco A",
        "sensors": ["Temperatura", "Umidade"]
    },
    {
        "name": "Servidor Central",
        "slug": "servidor-ti",
        "location": "Data Center",
        "sensors": ["Temperatura", "Consumo Energia"]
    },
    {
        "name": "Laboratório Química",
        "slug": "lab-quimica",
        "location": "Bloco C",
        "sensors": ["CO2", "Luminosidade"]
    },
    {
        "name": "Biblioteca",
        "slug": "biblioteca-geral",
        "location": "Área Comum",
        "sensors": ["Temperatura", "CO2"]
    }
]

# Especificações Técnicas dos Sensores
SENSOR_DEFS = {
    "Temperatura": {"unit": "°C", "min": 20.0, "max": 30.0},
    "Umidade": {"unit": "%", "min": 40.0, "max": 80.0},
    "CO2": {"unit": "ppm", "min": 400.0, "max": 900.0},
    "Luminosidade": {"unit": "lux", "min": 200.0, "max": 800.0},
    "Consumo Energia": {"unit": "kW", "min": 1.0, "max": 3.5}
}

def setup_infra():
    print("🔧 Sincronizando infraestrutura com a API...")
    
    # 1. Garante Tipos de Sensores
    tipos_existentes = {t['name']: t['id'] for t in requests.get(f"{API_URL}/sensor-types/").json()}
    mapa_tipos = {}
    
    for nome, specs in SENSOR_DEFS.items():
        if nome not in tipos_existentes:
            print(f"   + Criando Tipo: {nome}")
            res = requests.post(f"{API_URL}/sensor-types/", json={"name": nome, "unit": specs["unit"]})
            mapa_tipos[nome] = res.json()['id']
        else:
            mapa_tipos[nome] = tipos_existentes[nome]

    # 2. Garante Dispositivos
    devs_existentes = {d['slug']: d['id'] for d in requests.get(f"{API_URL}/devices/").json()}
    lista_simulacao = []

    for cenario in CENARIOS:
        if cenario['slug'] not in devs_existentes:
            print(f"   + Criando Device: {cenario['name']}")
            payload = {
                "name": cenario['name'], 
                "slug": cenario['slug'], 
                "location": cenario['location'], 
                "is_active": True
            }
            res = requests.post(f"{API_URL}/devices/", json=payload)
            d_id = res.json()['id']
        else:
            d_id = devs_existentes[cenario['slug']]
        
        # Prepara objeto para o loop
        lista_simulacao.append({
            "id": d_id,
            "name": cenario['name'],
            "sensors": cenario['sensors'] # Lista de nomes ["Temperatura", "CO2"]
        })
    
    return lista_simulacao, mapa_tipos

def run():
    devices, sensor_map = setup_infra()
    print(f"🚀 Simulando {len(devices)} dispositivos. Pressione Ctrl+C para parar.")
    
    try:
        while True:
            # Para cada dispositivo...
            for dev in devices:
                # Para cada sensor que ele tem...
                for sensor_name in dev['sensors']:
                    specs = SENSOR_DEFS[sensor_name]
                    
                    # Gera valor com leve flutuação
                    valor = random.uniform(specs['min'], specs['max'])
                    
                    # Refinamentos estéticos
                    if sensor_name == "CO2": valor = int(valor)
                    else: valor = round(valor, 2)

                    payload = {
                        "device_id": dev['id'],
                        "sensor_type_id": sensor_map[sensor_name],
                        "value": valor
                    }
                    
                    try:
                        requests.post(f"{API_URL}/measurements/", json=payload)
                        print(f"📡 {dev['name']} | {sensor_name}: {valor} {specs['unit']}")
                    except:
                        print("❌ Erro de conexão")
            
            # Espera 2 segundos antes da próxima rodada geral
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulação encerrada.")

if __name__ == "__main__":
    run()