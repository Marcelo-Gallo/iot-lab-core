from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.api import api_router
from app.core.database import init_db

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Cria as tabelas no banco de forma assíncrona
    await init_db()
    print("✅ Tabelas verificadas/criadas (Async).")
    
    yield # A aplicação roda aqui
    

    print("🛑 Encerrando aplicação.")

# --- APP SETUP ---
app = FastAPI(
    title="IoT Lab Core", 
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")