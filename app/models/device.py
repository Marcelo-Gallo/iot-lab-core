from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field

class Device(SQLModel, table=True):
	__tablename__ = "devices" #explicitando o nome da tabela
	
	id: Optional[int] = Field(default=None, primary_key=True)
	name: str = Field(index=True) #Ex -> ESP32 Estufa
	slug: str = Field(unique=True, index=True) #Ex -> esp32-estufa (Identificador único mais amigável, pra melhorar a dev experience e manutenção)
	location: Optional[str] = None #Ex -> Laboratório 1
	description: Optional[str] = None
	is_active: bool = Field(default=True)
	deleted_at: Optional[datetime] = Field(default=None)