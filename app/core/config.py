from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    # Variáveis de Aplicação
    PROJECT_NAME: str = "IoT Lab"
    API_V1_STR: str = "/api/v1"
    
    # Banco de Dados (Lê do .env)
    DATABASE_URL: str 

# Instância única para usar no projeto todo
settings = Settings()