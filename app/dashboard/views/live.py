import streamlit as st
import requests
import asyncio
import websockets
import json
import math
import pandas as pd
import altair as alt
from datetime import datetime
from app.dashboard.utils import API_URL, WS_URL, carregar_mapa_sensores, converter_para_local

# --- ESTILIZAÇÃO CSS ---
def inject_custom_css():
    st.markdown("""
    <style>
    div.device-card {
        background-color: #262730;
        border: 1px solid #464b5f;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER: CRIAR SPARKLINE COM EIXO Y ---
def make_sparkline(data_list, color_hex="#4E8CFF"):
    """
    Gera um gráfico miniatura, mas COM Eixo Y para contexto de escala.
    """
    if len(data_list) < 2:
        return None
    
    df_spark = pd.DataFrame({
        'step': range(len(data_list)),
        'value': data_list
    })
    
    # Define o domínio Y com uma pequena margem
    min_val = min(data_list)
    max_val = max(data_list)
    padding = (max_val - min_val) * 0.1 if max_val != min_val else 1.0
    
    chart = alt.Chart(df_spark).mark_line(
        interpolate='monotone', 
        strokeWidth=2,
        color=color_hex
    ).encode(
        x=alt.X('step', axis=None), # Eixo X (Tempo) oculto
        y=alt.Y(
            'value', 
            axis=alt.Axis(
                labels=True,      # Mostra números
                title=None,       # Sem título
                tickCount=3,      # Poucos ticks
                grid=True,        # Linhas guia
                domain=False,     # Sem linha vertical
                tickSize=0
            ),
            scale=alt.Scale(domain=[min_val - padding, max_val + padding])
        )
    ).configure_view(
        strokeWidth=0 # Remove borda externa
    ).properties(
        height=60, 
        width='container'
    )
    return chart

def get_devices_map():
    try:
        resp = requests.get(f"{API_URL}/devices/")
        if resp.status_code == 200:
            return {d['id']: d for d in resp.json()}
    except: pass
    return {}

# --- CORE DO DASHBOARD ---
async def run_live_dashboard(main_placeholder, location_filter):
    sensor_map = carregar_mapa_sensores()
    device_map = get_devices_map()
    
    # CSS Injetado aqui para garantir que carregue
    inject_custom_css()
    
    if not device_map:
        main_placeholder.warning("Nenhum dispositivo encontrado.")
        return

    # Inicializa Estado
    if "live_grid" not in st.session_state:
        st.session_state.live_grid = {}

    try:
        async with websockets.connect(WS_URL) as websocket:
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                dev_id = data['device_id']
                sens_id = data['sensor_type_id']
                val = data['value']
                dt = converter_para_local(data['created_at'])
                
                # Inicializa Device
                if dev_id not in st.session_state.live_grid:
                    st.session_state.live_grid[dev_id] = {'sensors': {}, 'last_seen': None}
                
                # Inicializa Sensor
                if sens_id not in st.session_state.live_grid[dev_id]['sensors']:
                    st.session_state.live_grid[dev_id]['sensors'][sens_id] = {
                        'value': val, 
                        'delta': 0, 
                        'history': []
                    }

                # Atualiza Dados
                sensor_state = st.session_state.live_grid[dev_id]['sensors'][sens_id]
                prev_val = sensor_state['value']
                
                sensor_state['value'] = val
                sensor_state['delta'] = val - prev_val
                sensor_state['ts'] = dt
                
                # Atualiza Histórico (Janela de 30 pontos)
                sensor_state['history'].append(val)
                if len(sensor_state['history']) > 30: 
                    sensor_state['history'].pop(0)

                st.session_state.live_grid[dev_id]['last_seen'] = dt

                # --- RENDERIZAÇÃO ---
                devices_to_show = []
                for d_id, d_info in device_map.items():
                    if location_filter != "Todas" and d_info.get('location') != location_filter:
                        continue
                    if d_id in st.session_state.live_grid:
                        devices_to_show.append(d_id)

                with main_placeholder.container():
                    if not devices_to_show:
                        st.info("Aguardando dados do enxame...")
                    else:
                        cols_per_row = 3
                        rows = math.ceil(len(devices_to_show) / cols_per_row)
                        
                        for r in range(rows):
                            cols = st.columns(cols_per_row)
                            for c in range(cols_per_row):
                                idx = r * cols_per_row + c
                                if idx < len(devices_to_show):
                                    d_id = devices_to_show[idx]
                                    d_meta = device_map.get(d_id, {'name': f'ID {d_id}', 'location': 'N/A'})
                                    d_live = st.session_state.live_grid[d_id]
                                    
                                    with cols[c]:
                                        with st.container(border=True):
                                            st.markdown(f"**🤖 {d_meta['name']}**")
                                            st.caption(f"📍 {d_meta.get('location', 'N/A')}")
                                            
                                            sorted_sensors = sorted(d_live['sensors'].items())
                                            
                                            if sorted_sensors:
                                                for sid, s_data in sorted_sensors:
                                                    s_info = sensor_map.get(sid, {'name': str(sid), 'unit': ''})
                                                    
                                                    # Valor Atual + Delta
                                                    st.metric(
                                                        label=s_info['name'],
                                                        value=f"{s_data['value']:.1f} {s_info['unit']}",
                                                        delta=f"{s_data['delta']:.2f}" if s_data['delta'] != 0 else None
                                                    )
                                                    
                                                    # Gráfico Sparkline
                                                    chart = make_sparkline(s_data['history'])
                                                    if chart:
                                                        st.altair_chart(chart, use_container_width=True)
                                                    st.divider()
                                            else:
                                                st.write("...")

                                            if d_live['last_seen']:
                                                last_ts = d_live['last_seen'].strftime("%H:%M:%S")
                                                st.caption(f"⏱️ {last_ts}")

    except Exception as e:
        main_placeholder.error(f"Erro WebSocket: {e}")
        if st.button("Reconectar"): st.rerun()

def render_live_view():
    st.title("⚡ Centro de Comando")
    
    device_map = get_devices_map()
    locations = sorted(list(set(d['location'] for d in device_map.values() if d.get('location'))))
    locations.insert(0, "Todas")
    
    st.sidebar.markdown("### 🕵️ Filtros")
    loc_filter = st.sidebar.selectbox("Localização", locations)
    
    # Placeholder único para atualização atômica
    main_placeholder = st.empty()
    asyncio.run(run_live_dashboard(main_placeholder, loc_filter))