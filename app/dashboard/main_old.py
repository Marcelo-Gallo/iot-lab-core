import streamlit as st
import requests
import pandas as pd
import asyncio
import websockets
import json
import time
from datetime import datetime, date, time as dt_time
import altair as alt

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Campus IoT Monitor", layout="wide", page_icon="🏫") 

API_URL = "http://backend:8000/api/v1"
WS_URL = "ws://backend:8000/api/v1/measurements/ws"

# --- 1. GERENCIAMENTO DE ESTADO ---
if "data_buffer" not in st.session_state: st.session_state.data_buffer = []
if "historico_data" not in st.session_state: st.session_state.historico_data = None
if "device_map" not in st.session_state: st.session_state.device_map = {}

# Estados CRUD
if "feedback_msg" not in st.session_state: st.session_state["feedback_msg"] = None
if "feedback_type" not in st.session_state: st.session_state["feedback_type"] = None
if "editing_id" not in st.session_state: st.session_state["editing_id"] = None

# --- 2. FUNÇÕES AUXILIARES ---
def carregar_mapa_sensores():
    try:
        res = requests.get(f"{API_URL}/sensor-types/")
        if res.status_code == 404: res = requests.get(f"{API_URL}/sensor_types/")
        if res.status_code == 200:
            return {t['id']: {'name': t['name'], 'unit': t['unit']} for t in res.json()}
    except: pass
    return {1: {'name': "Temperatura", 'unit': "°C"}, 2: {'name': "Umidade", 'unit': "%"}}

def atualizar_cache_mapas():
    s_map = carregar_mapa_sensores()
    d_map = {}
    active_ids = []
    try:
        res_d = requests.get(f"{API_URL}/devices/")
        if res_d.status_code == 200:
            for d in res_d.json():
                is_active = d.get('is_active', True)
                if d.get('deleted_at'): is_active = False
                d_map[d['id']] = {'name': d['name'], 'active': is_active}
                if is_active: active_ids.append(d['id'])
            st.session_state.device_map = d_map
    except: pass
    return s_map, d_map, active_ids

# --- FUNÇÕES CRUD ---
def submeter_formulario():
    payload = {
        "name": st.session_state.input_name,
        "slug": st.session_state.input_slug,
        "location": st.session_state.input_local,
        "is_active": True
    }
    try:
        response = requests.post(f"{API_URL}/devices/", json=payload)
        if response.status_code == 200:
            st.session_state["feedback_msg"] = f"Cadastrado: {payload['name']}"
            st.session_state["feedback_type"] = "success"
            st.session_state.input_name = ""
            st.session_state.input_slug = ""
            st.session_state.input_local = ""
        else:
            st.session_state["feedback_msg"] = f"Erro: {response.json().get('detail')}"
            st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro: {e}"
        st.session_state["feedback_type"] = "error"

def alternar_status_dispositivo(device_id, novo_status):
    try:
        payload = {"is_active": novo_status, "deleted_at": None if novo_status else None}
        msg = "Restaurado!" if novo_status else "Arquivado."
        res = requests.patch(f"{API_URL}/devices/{device_id}", json=payload)
        if res.status_code == 200:
            st.session_state["feedback_msg"] = msg
            st.session_state["feedback_type"] = "success"
        else:
            st.session_state["feedback_msg"] = f"Erro: {res.text}"
            st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro: {e}"
        st.session_state["feedback_type"] = "error"

# --- 3. CORE DO WEBSOCKET ---
async def listen_to_ws(kpi_container, charts_placeholder):
    # Setup inicial
    sensor_map, device_map, active_ids = atualizar_cache_mapas()
    
    def renderizar_buffer(current_device_map, current_active_ids):
        if not st.session_state.data_buffer: return
        
        df = pd.DataFrame(st.session_state.data_buffer)
        df = df[df['Device ID'].isin(current_active_ids)]
        if df.empty: return

        # Tradução de nomes (Anti-Fantasma de Dados)
        mapa_nomes_atual = {id: info['name'] for id, info in current_device_map.items()}
        df['Device'] = df['Device ID'].map(mapa_nomes_atual).fillna(df['Device ID'].astype(str))

        latest = df.tail(20).drop_duplicates(subset=['Sensor', 'Device'], keep='last')
        
        with kpi_container.container():
            tipos = latest['Sensor'].unique()
            cols = st.columns(len(tipos)) if len(tipos) > 0 else [st.empty()]
            for i, tipo in enumerate(tipos):
                subset = latest[latest['Sensor'] == tipo]
                avg = subset['Valor'].mean()
                unit = subset['Unidade'].iloc[0]
                cols[i].metric(f"Média {tipo}", f"{avg:.1f} {unit}")

        with charts_placeholder.container():
            for tipo in tipos:
                df_tipo = df[df['Sensor'] == tipo]
                unit = df_tipo['Unidade'].iloc[0]
                st.markdown(f"#### {tipo} ({unit})")
                
                # KEY ÚNICA com Timestamp para forçar recriação do componente
                chart_key = f"live_chart_{tipo}_{int(time.time())}"
                
                chart = alt.Chart(df_tipo).mark_line(point=True).encode(
                    x=alt.X('Hora', axis=alt.Axis(title='')),
                    y=alt.Y('Valor', axis=alt.Axis(title=None), scale=alt.Scale(zero=False)),
                    color=alt.Color('Device', legend=alt.Legend(title="Local")),
                    tooltip=['Hora', 'Device', 'Valor']
                ).properties(height=200)
                st.altair_chart(chart, use_container_width=True, key=chart_key)

    # Backfill
    if len(st.session_state.data_buffer) < 50:
        try:
            res = requests.get(f"{API_URL}/measurements/?limit=100")
            if res.status_code == 200:
                history = res.json()
                for data in reversed(history):
                    d_id = data['device_id']
                    if d_id not in active_ids: continue 
                    s_id = data['sensor_type_id']
                    s_info = sensor_map.get(s_id, {'name': f"S{s_id}", 'unit': ''})
                    d_info = device_map.get(d_id, {'name': f"ID {d_id}", 'active': True})

                    st.session_state.data_buffer.append({
                        "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                        "Valor": data["value"],
                        "Sensor": s_info['name'],
                        "Unidade": s_info['unit'],
                        "Device": d_info['name'],
                        "Device ID": d_id
                    })
                renderizar_buffer(device_map, active_ids)
        except: pass

    # Loop WebSocket
    last_update_time = time.time()
    map_refresh_time = time.time()
    UPDATE_DELAY = 0.7 
    MAP_REFRESH_DELAY = 1.0

    try:
        async with websockets.connect(WS_URL) as websocket:
            while True:
                # PEQUENA PAUSA: Permite que o Streamlit interrompa o loop se a aba mudar
                await asyncio.sleep(0.01) 
                
                msg = await websocket.recv()
                data = json.loads(msg)
                
                if (time.time() - map_refresh_time) > MAP_REFRESH_DELAY:
                    sensor_map, device_map, active_ids = atualizar_cache_mapas()
                    map_refresh_time = time.time()

                s_id = data['sensor_type_id']
                d_id = data['device_id']

                if d_id not in active_ids: continue
                
                s_info = sensor_map.get(s_id, {'name': f"S{s_id}", 'unit': ''})
                st.session_state.data_buffer.append({
                    "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                    "Valor": data["value"],
                    "Sensor": s_info['name'],
                    "Unidade": s_info['unit'],
                    "Device": "Loading...", 
                    "Device ID": d_id
                })
                
                if len(st.session_state.data_buffer) > 300:
                    st.session_state.data_buffer.pop(0)

                current_time = time.time()
                if (current_time - last_update_time) > UPDATE_DELAY:
                    renderizar_buffer(device_map, active_ids)
                    last_update_time = current_time

    except (websockets.exceptions.ConnectionClosed, OSError):
        st.error("Conexão WebSocket perdida.")
    # StopException passa direto aqui e encerra o loop

# ==========================================================
# UI & NAVEGAÇÃO
# ==========================================================
st.sidebar.title("🏫 Campus IoT")
menu_options = ["Monitoramento (Live)", "Histórico (Análise)", "Gerenciamento (CRUD)"]
choice = st.sidebar.radio("Navegação", menu_options)
st.sidebar.markdown("---")

# --- MASTER CONTAINER (A SOLUÇÃO DEFINITIVA) ---
# Criamos um placeholder gigante que ocupa a página inteira.
# Quando o script roda de novo, esse placeholder é recriado, 
# limpando qualquer lixo visual (fantasmas) da execução anterior.
main_placeholder = st.empty()

with main_placeholder.container():

    # 1. LIVE
    if choice == "Monitoramento (Live)":
        st.title("📡 Monitoramento em Tempo Real")
        kpi_box = st.empty() 
        st.divider()
        charts_box = st.empty()
        # Roda o loop
        asyncio.run(listen_to_ws(kpi_box, charts_box))

    # 2. HISTÓRICO
    elif choice == "Histórico (Análise)":
        st.title("📊 Análise Comparativa")
        
        sensor_map, device_map, active_ids = atualizar_cache_mapas()
        d_options = {v['name']: k for k, v in device_map.items() if v['active']}

        with st.expander("🔎 Filtros", expanded=True):
            c1, c2, c3 = st.columns([1, 1, 1])
            dates = c1.date_input("Período", (date.today(), date.today()))
            devs = c2.multiselect("Dispositivos", options=d_options.keys())
            limit = c3.number_input("Limite", value=1000, step=500)
            btn = st.button("Buscar", type="primary", use_container_width=True)

        if btn:
            try:
                start_dt = datetime.combine(dates[0], dt_time.min)
                end_dt = datetime.combine(dates[1], dt_time.max)
                params = {"start_date": start_dt.isoformat(), "end_date": end_dt.isoformat(), "limit": limit}
                if devs: params["device_ids"] = [d_options[k] for k in devs]
                
                res = requests.get(f"{API_URL}/measurements/", params=params)
                data = res.json()
                
                if data:
                    if len(data) >= limit: st.warning(f"⚠️ Limite de {limit} atingido.")
                    else: st.success(f"{len(data)} registros carregados.")
                    
                    rev_d_map = {k: v['name'] for k, v in device_map.items()}
                    processed = []
                    for row in data:
                        d_id = row['device_id']
                        if d_id not in active_ids: continue

                        s = sensor_map.get(row['sensor_type_id'], {'name': '?', 'unit': ''})
                        d_name = rev_d_map.get(d_id, f"ID {d_id}")
                        processed.append({
                            "Data": row['created_at'], "Valor": row['value'],
                            "Sensor": s['name'], "Unidade": s['unit'], "Dispositivo": d_name
                        })
                    
                    if processed:
                        df = pd.DataFrame(processed)
                        df['Data'] = pd.to_datetime(df['Data'])
                        st.session_state.historico_data = df
                    else:
                        st.warning("Dados pertencem a dispositivos arquivados.")
                        st.session_state.historico_data = None
                else:
                    st.warning("Sem dados.")
                    st.session_state.historico_data = None
            except Exception as e: st.error(f"Erro: {e}")

        if st.session_state.historico_data is not None:
            df = st.session_state.historico_data
            sensores = df['Sensor'].unique()
            st.divider()
            for sensor in sensores:
                df_s = df[df['Sensor'] == sensor]
                unit = df_s.iloc[0]['Unidade']
                st.markdown(f"### 📈 {sensor} ({unit})")
                
                k1, k2, k3 = st.columns(3)
                k1.metric("Média", f"{df_s['Valor'].mean():.2f}")
                k2.metric("Max", f"{df_s['Valor'].max()}")
                k3.metric("Min", f"{df_s['Valor'].min()}")
                
                hist_chart_key = f"hist_chart_{sensor}_{int(time.time())}"
                
                chart = alt.Chart(df_s).mark_line(point=True).encode(
                    x=alt.X('Data', axis=alt.Axis(format='%d/%m %H:%M', title='')),
                    y=alt.Y('Valor', title=None, scale=alt.Scale(zero=False)),
                    color='Dispositivo', tooltip=['Data', 'Dispositivo', 'Valor']
                ).properties(height=300).interactive()
                st.altair_chart(chart, use_container_width=True, key=hist_chart_key)
                st.divider()
            with st.expander("Dados Brutos"): st.dataframe(df, use_container_width=True)

    # 3. CRUD
    elif choice == "Gerenciamento (CRUD)":
        st.title("📡 Gerenciamento de Dispositivos")
        if st.session_state["feedback_msg"]:
            if st.session_state["feedback_type"] == "success": st.success(st.session_state["feedback_msg"])
            else: st.error(st.session_state["feedback_msg"])
            st.session_state["feedback_msg"] = None

        with st.form("cad"):
            c1, c2 = st.columns(2)
            st.session_state.input_name = c1.text_input("Nome", key="in_nm")
            st.session_state.input_slug = c2.text_input("Slug", key="in_sl")
            st.session_state.input_local = st.text_input("Local", key="in_lc")
            st.form_submit_button("Cadastrar", on_click=submeter_formulario)
        st.divider()
        
        try:
            res = requests.get(f"{API_URL}/devices/")
            devices = res.json() if res.status_code == 200 else []
        except: devices = []
        
        if devices:
            cols = st.columns([0.5, 2, 2, 2, 1, 1.5])
            cols[0].write("**ID**"); cols[1].write("**Nome**"); cols[2].write("**Slug**"); 
            cols[3].write("**Local**"); cols[4].write("**Status**"); cols[5].write("**Ações**")
            st.write("---")
            for d in devices:
                is_active = d.get('is_active', True)
                if d.get('deleted_at'): is_active = False
                
                if st.session_state["editing_id"] == d["id"]:
                    with st.form(f"e_{d['id']}"):
                        c = st.columns(3)
                        nn = c[0].text_input("N", d["name"])
                        ns = c[1].text_input("S", d["slug"])
                        nl = c[2].text_input("L", d["location"])
                        if st.form_submit_button("💾"):
                            requests.patch(f"{API_URL}/devices/{d['id']}", json={"name":nn,"slug":ns,"location":nl})
                            st.session_state["editing_id"] = None
                            st.session_state["feedback_msg"] = "Salvo!"; st.session_state["feedback_type"] = "success"
                            st.rerun()
                else:
                    c = st.columns([0.5, 2, 2, 2, 1, 1.5])
                    c[0].write(d['id']); c[1].write(d['name']); c[2].code(d['slug']); c[3].write(d['location'])
                    c[4].write("🟢" if is_active else "🔴 Arquivado")
                    b1, b2 = c[5].columns(2)
                    if b1.button("✏️", key=f"ed_{d['id']}"): st.session_state["editing_id"] = d["id"]; st.rerun()
                    if is_active:
                        if b2.button("🗑️", key=f"rm_{d['id']}", help="Arquivar"): 
                            alternar_status_dispositivo(d['id'], False); st.rerun()
                    else:
                        if b2.button("🔄", key=f"res_{d['id']}", help="Restaurar"): 
                            alternar_status_dispositivo(d['id'], True); st.rerun()