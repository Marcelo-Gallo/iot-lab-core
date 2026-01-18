import streamlit as st
import requests
import pandas as pd
import asyncio
import websockets
import json
import altair as alt
from app.dashboard.utils import API_URL, WS_URL, carregar_mapa_sensores, converter_para_local

async def listen_to_ws(kpi_container, chart_container, history_container):
    try:
        sensor_map = carregar_mapa_sensores()
        
        # Buffer de estado
        if "data_buffer" not in st.session_state:
            st.session_state.data_buffer = []

        # Backfill
        if not st.session_state.data_buffer:
            try:
                res = requests.get(f"{API_URL}/measurements/?limit=50")
                if res.status_code == 200:
                    history_data = res.json()
                    for data in reversed(history_data):
                        s_id = data['sensor_type_id']
                        info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                        dt_local = converter_para_local(data["created_at"])
                        st.session_state.data_buffer.append({
                            "Hora": dt_local.strftime("%H:%M:%S"),
                            "Valor": data["value"],
                            "Sensor": info['name'],
                            "Unidade": info['unit']
                        })
            except: pass

        async with websockets.connect(WS_URL) as websocket:
            latest_values = {}
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                s_id = data['sensor_type_id']
                latest_values[s_id] = data['value']
                info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                dt_local = converter_para_local(data["created_at"])

                st.session_state.data_buffer.append({
                    "Hora": dt_local.strftime("%H:%M:%S"),
                    "Valor": data["value"],
                    "Sensor": info['name'],
                    "Unidade": info['unit']
                })
                
                if len(st.session_state.data_buffer) > 50:
                    st.session_state.data_buffer.pop(0)

                df = pd.DataFrame(st.session_state.data_buffer)
                
                # Renderiza KPIs
                with kpi_container.container():
                    cols = st.columns(len(latest_values) + 1)
                    for i, (sid, val) in enumerate(latest_values.items()):
                        inf = sensor_map.get(sid, {'name':'?', 'unit':''})
                        cols[i].metric(f"📡 {inf['name']}", f"{val:.1f} {inf['unit']}")
                    cols[-1].metric("⏱️ Live", dt_local.strftime("%H:%M:%S"))

                # Renderiza Gráfico
                with chart_container:
                    st.line_chart(data=df, x="Hora", y="Valor", color="Sensor")
                
                # Tabela simples
                with history_container:
                     st.dataframe(df[::-1], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Conexão perdida: {e}")

def render_live_view():
    st.title("⚡ Monitoramento em Tempo Real")
    kpi_container = st.empty()
    chart_container = st.empty()
    st.write("### 📋 Buffer Recente")
    history_container = st.empty()
    
    asyncio.run(listen_to_ws(kpi_container, chart_container, history_container))