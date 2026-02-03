import requests
import time
import random
from datetime import datetime, timezone

# ================= CONFIGURAÇÃO =================
DEVICE_TOKEN = "sk_iot_zkPAWjGzJ-T7P0PFHAZkyQioft2rgoTVvRH2-TwEmKI" 
SENSORS = [
    {"id": 1, "min": 20.0, "max": 30.0, "name": "Temperatura"},
    {"id": 2, "min": 40.0, "max": 60.0, "name": "Umidade"}
]
API_URL = "http://localhost:8000/api/v1/measurements/"
# ================================================

def send_data():
    headers = {
        "X-Device-Token": DEVICE_TOKEN,
        "Content-Type": "application/json"
    }

    print(f"📡 Simulador IoT (Token-Based Auth)")
    print(f"🔑 Usando Token: {DEVICE_TOKEN[:10]}...")
    
    try:
        while True:
            for sensor in SENSORS:
                # Payload limpo: Sensor + Valor
                payload = {
                    "sensor_type_id": sensor["id"],
                    "value": round(random.uniform(sensor["min"], sensor["max"]), 2),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                try:
                    res = requests.post(API_URL, json=payload, headers=headers)
                    
                    if res.status_code == 200:
                        # O backend confirma quem somos na resposta
                        dev_id = res.json().get('device_id')
                        print(f"✅ Aceito pelo Device {dev_id}: {payload['value']}")
                    elif res.status_code == 401:
                        print("⛔ Token Recusado (401)")
                        return
                    else:
                        print(f"⚠️  Erro {res.status_code}: {res.text}")
                        
                except Exception as e:
                    print(f"❌ Erro de conexão: {e}")

            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Encerrado.")

if __name__ == "__main__":
    send_data()