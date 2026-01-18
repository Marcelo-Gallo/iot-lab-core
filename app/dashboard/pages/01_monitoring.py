import streamlit as st
import asyncio
import websockets
import json
import pandas as pd
import time
import altair as alt
from datetime import datetime
# Importando do nosso novo Service (ajuste o caminho no sys.path se precisar, ou use import relativo)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.api_service import get_active_devices_map, carregar_mapa_sensores

st.set_page_config(page_title="Monitoramento Live", layout="wide")
st.title("📡 Monitoramento em Tempo Real")

WS_URL = "ws://backend:8000/api/v1/measurements/ws"

if "data_buffer" not in st.session_state: st.session_state.data_buffer = []

# --- LÓGICA DE RENDERIZAÇÃO ---
def renderizar(kpi, charts, d_map, active_ids):
    if not st.session_state.data_buffer: return
    df = pd.DataFrame(st.session_state.data_buffer)
    df = df[df['Device ID'].isin(active_ids)]
    if df.empty: return

    # Tradução Dinâmica
    mapa_nomes = {id: info['name'] for id, info in d_map.items()}
    df['Device'] = df['Device ID'].map(mapa_nomes).fillna(df['Device ID'].astype(str))

    latest = df.tail(20).drop_duplicates(subset=['Sensor', 'Device'], keep='last')
    
    with kpi.container():
        tipos = latest['Sensor'].unique()
        cols = st.columns(len(tipos)) if len(tipos) > 0 else [st.empty()]
        for i, tipo in enumerate(tipos):
            subset = latest[latest['Sensor'] == tipo]
            cols[i].metric(f"Média {tipo}", f"{subset['Valor'].mean():.1f} {subset['Unidade'].iloc[0]}")

    with charts.container():
        for tipo in tipos:
            df_t = df[df['Sensor'] == tipo]
            st.markdown(f"#### {tipo}")
            c = alt.Chart(df_t).mark_line(point=True).encode(
                x=alt.X('Hora', axis=alt.Axis(title='')),
                y=alt.Y('Valor', scale=alt.Scale(zero=False)),
                color='Device', tooltip=['Hora', 'Device', 'Valor']
            ).properties(height=200)
            st.altair_chart(c, use_container_width=True)

async def run_ws():
    kpi_box = st.empty()
    st.divider()
    charts_box = st.empty()
    
    sensor_map = carregar_mapa_sensores()
    d_map, active_ids = get_active_devices_map()
    
    last_update = time.time()
    
    try:
        async with websockets.connect(WS_URL) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                # Atualiza mapas a cada 2s (simples)
                if time.time() - last_update > 2.0:
                    d_map, active_ids = get_active_devices_map()
                
                if data['device_id'] not in active_ids: continue
                
                s_info = sensor_map.get(data['sensor_type_id'], {'name': '?', 'unit': ''})
                
                st.session_state.data_buffer.append({
                    "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                    "Valor": data["value"],
                    "Sensor": s_info['name'],
                    "Unidade": s_info['unit'],
                    "Device ID": data['device_id']
                })
                
                if len(st.session_state.data_buffer) > 300: st.session_state.data_buffer.pop(0)
                
                if time.time() - last_update > 0.7:
                    renderizar(kpi_box, charts_box, d_map, active_ids)
                    last_update = time.time()
                    
    except Exception:
        st.error("Conexão perdida.")

asyncio.run(run_ws())