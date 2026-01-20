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
    
    # Banco de Dados
    DATABASE_URL: str 

    SECRET_KEY: str = "1d0ea4e18efb85aba62bdca61100f0b5db8735c6098bc71701fa0a39b173ce26" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# Instância única
settings = Settings()