from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError, EmailStr, AnyHttpUrl
from typing import List, Union

class Settings(BaseSettings):
    # Configuração do Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore" # Ignora variáveis extras no .env sem dar erro
    )

    # --- Aplicação ---
    PROJECT_NAME: str = "IoT Lab Core"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # --- Banco de Dados (Docker Friendly) ---
    # Ao invés de forçar você a escrever a URL completa no .env,
    # montamos ela aqui usando as peças individuais.
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        """Monta a string de conexão Async automaticamente"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # --- Segurança ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 dias

    # Validação de Segurança que você já tinha (MANTIDA)
    @field_validator("SECRET_KEY")
    @classmethod
    def check_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("A SECRET_KEY deve ter no mínimo 32 caracteres para segurança criptográfica.")
        return v
    
    # --- CORS (Permite conexão do Frontend) ---
    # Aceita string separada por vírgula ou lista JSON
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # --- SEED (O QUE FALTAVA PARA FUNCIONAR) ---
    FIRST_SUPERUSER: EmailStr = "admin@iotlab.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"


# Bloco de inicialização segura (MANTIDO DO SEU CÓDIGO)
try:
    settings = Settings()
except ValidationError as e:
    print("\n🚨 ERRO CRÍTICO DE CONFIGURAÇÃO 🚨")
    print("O sistema não pode iniciar porque variáveis obrigatórias estão ausentes.")
    print("Verifique se seu .env possui: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_DB e SECRET_KEY")
    print("-" * 50)
    print(e)
    print("-" * 50)
    raise e