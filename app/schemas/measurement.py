from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# O que o sensor envia (Payload)
class MeasurementCreate(BaseModel):
    device_id: int
    sensor_type_id: int
    value: float

# O que a API responde (inclui ID e Data)
class MeasurementPublic(MeasurementCreate):
    id: int
    created_at: datetime

class MeasurementAnalytics(BaseModel):
    bucket: datetime       # A "fatia" de tempo (ex: 10:00, 11:00, 12:00)
    sensor_type_id: int    # De qual sensor é essa média?
    avg_value: float       # O valor médio naquele período
    min_value: float       # (Opcional) Mínima para desenhar "sombra" no gráfico
    max_value: float       # (Opcional) Máxima
    count: int             # Quantas leituras compõem essa média (confiabilidade)