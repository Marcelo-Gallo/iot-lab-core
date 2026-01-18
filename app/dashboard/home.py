import streamlit as st

# 1. A CURA DO ZOOM OUT: Layout Wide na Home também!
st.set_page_config(page_title="IoT Lab Core", layout="wide", page_icon="🏫")

import sys
import os
import time

# Ajuste de path para importar services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.api_service import get_all_devices, fetch_historical_data

# --- CABEÇALHO ---
st.title("🏫 Campus IoT Core")
st.markdown("#### Central de Comando e Status do Sistema")
st.divider()

# --- 1. HEALTH CHECK (Teste de Conexão) ---
api_status = "Desconhecido"
db_latency = 0
try:
    start = time.time()
    # Tenta buscar 1 registro só para testar a rota e o banco
    fetch_historical_data({"limit": 1})
    end = time.time()
    db_latency = (end - start) * 1000 # ms
    api_status = "Online"
    status_color = "green"
except:
    api_status = "Offline / Erro"
    status_color = "red"

# --- 2. CÁLCULO DE MÉTRICAS ---
devices = get_all_devices()
total_dev = len(devices)
ativos = len([d for d in devices if d.get('is_active', True) and not d.get('deleted_at')])
arquivados = total_dev - ativos

# --- 3. EXIBIÇÃO ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Status da API", api_status, f"{db_latency:.0f}ms", delta_color="normal" if api_status == "Online" else "inverse")

with col2:
    st.metric("Total Dispositivos", total_dev)

with col3:
    st.metric("🟢 Em Operação", ativos)

with col4:
    st.metric("🔴 Arquivados", arquivados)

st.divider()

# --- 4. VISÃO GERAL (Opcional, mas útil para TCC/Doc) ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("🗺️ Arquitetura do Sistema")
    st.markdown("""
    Este sistema utiliza uma arquitetura de microsserviços containerizada:
    
    * **Backend:** FastAPI (Python) gerenciando regras de negócio e banco de dados.
    * **Database:** PostgreSQL armazenando dados relacionais e séries temporais.
    * **Frontend:** Streamlit para visualização de dados e gestão (CRUD).
    * **Comunicação:** * *Sensores -> API:* HTTP POST (REST).
        * *API -> Dashboard:* WebSocket (Tempo Real).
    """)
    
    st.info(f"📍 Versão do Sistema: **v2.5 (Stable)** | Ambiente: **Production (Docker)**")

with c2:
    st.subheader("🔗 Acesso Rápido")
    st.markdown("""
    Use o menu lateral para navegar:
    
    * **📡 Monitoramento:** Acompanhe os sensores em tempo real.
    * **📊 Histórico:** Exporte dados para CSV/Excel.
    * **⚙️ Gerenciamento:** Adicione ou remova sensores.
    """)
    
    if api_status != "Online":
        st.error("⚠️ ALERTA: Não foi possível conectar ao Backend. Verifique se o container 'backend' está rodando.")