from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configurações Gerais
    PROJECT_NAME: str = "IoT Lab"
    API_V1_STR: str = "/api/v1"
    
    # Banco de Dados
    DATABASE_URL: str # O Pydantic busca a var no .env

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra="ignore"

# Instância única para usar no projeto todo
settings = Settings()