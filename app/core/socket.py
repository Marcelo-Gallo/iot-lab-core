from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Lista para guardar quem está conectado
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 Cliente conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Cliente desconectado. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Envia uma mensagem para TODOS os conectados"""
        # Itera sobre uma cópia da lista para evitar erros se alguém sair durante o envio
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Se der erro (cliente fechou o browser abruptamente), removemos da lista
                print(f"⚠️ Erro ao enviar WS: {e}")
                self.disconnect(connection)

# Instância Global (Singleton)
manager = ConnectionManager()