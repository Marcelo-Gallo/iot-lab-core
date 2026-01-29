from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    # Variáveis de Aplicação
    PROJECT_NAME: str = "IoT Lab"
    API_V1_STR: str = "/api/v1"
    
    # Banco de Dados
    DATABASE_URL: str 
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DEBUG: bool = True

    @field_validator("SECRET_KEY")
    @classmethod
    def check_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("A SECRET_KEY deve ter no mínimo 32 caracteres para segurança criptográfica.")
        return v

# Bloco de inicialização segura
try:
    # Instancia Unica
    settings = Settings()
except ValidationError as e:
    print("\n ERRO CRÍTICO DE CONFIGURAÇÃO ")
    print("O sistema não pode iniciar porque variáveis obrigatórias estão ausentes.")
    print("Verifique seu arquivo .env ou as variáveis de ambiente do container.")
    print("-" * 50)
    print(e)
    print("-" * 50)
    exit(1) # Encerra o processo com código de erro