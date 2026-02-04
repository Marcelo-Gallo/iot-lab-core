from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, organization_id: int):
        await websocket.accept()
        if organization_id not in self.active_connections:
            self.active_connections[organization_id] = []
        
        self.active_connections[organization_id].append(websocket)
        print(f"🔌 Cliente conectado na Org {organization_id}. Total nesta sala: {len(self.active_connections[organization_id])}")

    def disconnect(self, websocket: WebSocket, organization_id: int):
        if organization_id in self.active_connections:
            if websocket in self.active_connections[organization_id]:
                self.active_connections[organization_id].remove(websocket)
                print(f"❌ Cliente desconectado da Org {organization_id}.")
                
                if not self.active_connections[organization_id]:
                    del self.active_connections[organization_id]

    async def broadcast(self, message: dict, organization_id: int):
        """
        Envia mensagem APENAS para conexões da organização especificada.
        Implementa o Isolamento Vertical no nível de transporte.
        """
        if organization_id not in self.active_connections:
            return

        for connection in self.active_connections[organization_id][:]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️ Erro ao enviar WS na Org {organization_id}: {e}")
                self.disconnect(connection, organization_id)

manager = ConnectionManager()