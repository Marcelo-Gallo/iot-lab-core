import streamlit as st
import requests
import pandas as pd
import asyncio
import websockets
import json
import altair as alt
import pytz 
from datetime import datetime

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Laboratório IoT", layout="wide") 

API_URL = "http://backend:8000/api/v1"
WS_URL = "ws://backend:8000/api/v1/measurements/ws"
FUSO_BR = pytz.timezone("America/Sao_Paulo")

# --- ESTADOS ---
if "feedback_msg" not in st.session_state: st.session_state["feedback_msg"] = None
if "feedback_type" not in st.session_state: st.session_state["feedback_type"] = None
if "editing_id" not in st.session_state: st.session_state["editing_id"] = None
if "data_buffer" not in st.session_state: st.session_state.data_buffer = []

# --- FUNÇÕES AUXILIARES ---
def converter_para_local(iso_str):
    if not iso_str: return None
    dt_utc = datetime.fromisoformat(iso_str).replace(tzinfo=pytz.UTC)
    return dt_utc.astimezone(FUSO_BR)

def carregar_mapa_sensores():
    """
    Retorna dicionário rico: {id: {'name': 'Temperatura', 'unit': '°C'}}
    Busca direto do banco, eliminando hardcoding.
    """
    try:
        response = requests.get(f"{API_URL}/sensor-types/")
        if response.status_code == 200:
            tipos = response.json()
            # Mapeia ID -> Objeto com Nome e Unidade
            return {
                t['id']: {'name': t['name'], 'unit': t['unit']} 
                for t in tipos
            }
    except:
        pass
    # Fallback 
    return {1: {'name': "Temperatura", 'unit': "°C"}, 2: {'name': "Umidade", 'unit': "%"}}

def submeter_formulario():
    payload = {
        "name": st.session_state.input_name,
        "slug": st.session_state.input_slug,
        "location": st.session_state.input_local,
    }
    try:
        response = requests.post(f"{API_URL}/devices/", json=payload)
        if response.status_code == 200:
            st.session_state["feedback_msg"] = f"Dispositivo '{payload['name']}' cadastrado!"
            st.session_state["feedback_type"] = "success"
            st.session_state.input_name = ""; st.session_state.input_slug = ""; st.session_state.input_local = ""
        else:
            err = response.json().get('detail', 'Erro')
            st.session_state["feedback_msg"] = f"Erro: {err}"; st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro Conexão: {e}"; st.session_state["feedback_type"] = "error"

def deletar_dispositivo(device_id):
    try:
        response = requests.delete(f"{API_URL}/devices/{device_id}")
        if response.status_code == 200:
            st.session_state["feedback_msg"] = "Dispositivo arquivado."; st.session_state["feedback_type"] = "warning"
        else:
            st.session_state["feedback_msg"] = f"Erro: {response.text}"; st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro: {e}"; st.session_state["feedback_type"] = "error"

# --- WEBSOCKET ---
async def listen_to_ws(kpi_container, chart_container, log_container, history_container):
    try:
        sensor_map = carregar_mapa_sensores()
        
        # Backfill
        if not st.session_state.data_buffer:
            try:
                res = requests.get(f"{API_URL}/measurements/?limit=50")
                if res.status_code == 200:
                    history_data = res.json()
                    for data in reversed(history_data):
                        s_id = data['sensor_type_id']
                        # Usa o mapa rico ou default
                        info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                        
                        dt_local = converter_para_local(data["created_at"])
                        st.session_state.data_buffer.append({
                            "Hora": dt_local.strftime("%H:%M:%S"),
                            "Valor": data["value"],
                            "Sensor": info['name'],
                            "Device ID": f"{data['device_id']}",
                            "Unidade": info['unit']
                        })
            except Exception as e:
                print(f"Erro backfill: {e}")

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
                    "Device ID": f"{data['device_id']}",
                    "Unidade": info['unit']
                })
                
                if len(st.session_state.data_buffer) > 50:
                    st.session_state.data_buffer.pop(0)

                df = pd.DataFrame(st.session_state.data_buffer)
                
                with kpi_container.container():
                    qtd = len(latest_values)
                    cols = st.columns(qtd + 1)
                    for i, (sens_id, valor) in enumerate(latest_values.items()):
                        info = sensor_map.get(sens_id, {'name': f"Sensor {sens_id}", 'unit': ''})
                        cols[i].metric(label=f"📡 {info['name']}", value=f"{valor:.1f} {info['unit']}")
                    
                    cols[-1].metric("⏱️ Monitoramento", dt_local.strftime("%H:%M:%S"), delta=f"ID: {data['device_id']}", delta_color="off")

                with chart_container:
                    st.line_chart(data=df, x="Hora", y="Valor", color="Sensor")

                with history_container:
                    st.dataframe(df[::-1][["Hora", "Sensor", "Valor", "Device ID"]], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Conexão perdida: {e}")

# ==========================================================
# UI PRINCIPAL
# ==========================================================
st.sidebar.title("🔌 IoT Lab Core")
st.sidebar.markdown("---")
menu_options = ["Monitoramento (Live)", "Histórico (Analytics)", "Gerenciamento (CRUD)"]
choice = st.sidebar.radio("Navegação", menu_options)
st.sidebar.markdown("---")
st.sidebar.info("Sistema v3.1 | Dynamic Units & KPI Fix")

if choice == "Monitoramento (Live)":
    st.title("⚡ Monitoramento em Tempo Real")
    kpi_container = st.empty()
    chart_container = st.empty()
    st.write("### 📋 Buffer Recente")
    history_container = st.empty()
    asyncio.run(listen_to_ws(kpi_container, chart_container, st.empty(), history_container))

elif choice == "Histórico (Analytics)":
    st.title("📊 Análise Inteligente de Dados")
    
    with st.expander("⚙️ Configuração", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            periodo = st.selectbox("Janela", ["1h", "1d", "1w", "1m"], format_func=lambda x: {"1h":"1 Hora", "1d":"24 Horas", "1w":"1 Semana", "1m":"1 Mês"}[x])
        with c2:
            default_idx = 0 if periodo == '1h' else 1 if periodo == '1d' else 2
            bucket = st.selectbox("Resolução", ["minute", "hour", "day"], index=default_idx, format_func=lambda x: {"minute":"Minuto", "hour":"Hora", "day":"Dia"}[x])
        with c3:
            st.write(""); st.write("")
            btn_update = st.button("🔄 Analisar", type="primary", use_container_width=True)

    if btn_update:
        try:
            sensor_map = carregar_mapa_sensores()
            params = {"period": periodo, "bucket_size": bucket}
            res = requests.get(f"{API_URL}/measurements/analytics/", params=params)
            
            if res.status_code == 200:
                data = res.json()
                if not data:
                    st.warning("Sem dados.")
                else:
                    rows = []
                    for item in data:
                        s_id = item['sensor_type_id']
                        info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                        dt_local = converter_para_local(item['bucket'])
                        
                        rows.append({
                            "Data": dt_local,
                            "Sensor": info['name'],
                            "Unidade": info['unit'],
                            "Média": item['avg_value'],
                            "Mínima": item['min_value'],
                            "Máxima": item['max_value'],
                            "Amostras": item['count']
                        })
                    
                    df = pd.DataFrame(rows)
                    
                    st.divider()
                    st.write("### 🧠 Insights por Sensor")
                    
                    sensores_unicos = df['Sensor'].unique()
                    
                    cols_stats = st.columns(len(sensores_unicos))
                    
                    for i, sensor_nome in enumerate(sensores_unicos):
                        df_s = df[df['Sensor'] == sensor_nome]
                        
                        media_periodo = df_s['Média'].mean()
                        max_periodo = df_s['Máxima'].max()
                        min_periodo = df_s['Mínima'].min()
                        unidade_s = df_s.iloc[0]['Unidade']
                        
                        with cols_stats[i]:
                            st.markdown(f"**📡 {sensor_nome}**")
                            st.metric("Média", f"{media_periodo:.2f} {unidade_s}")
                            st.caption(f"Max: {max_periodo} | Min: {min_periodo}")
                            
                    st.divider()

                    # --- GRÁFICO COM PICOS ---
                    tab1, tab2 = st.tabs(["📈 Tendência", "📋 Dados Brutos"])
                    with tab1:
                        # Base do gráfico
                        base = alt.Chart(df).encode(x=alt.X('Data', title='Tempo (BRT)', axis=alt.Axis(format='%H:%M')))

                        # Linha da Média
                        line = base.mark_line().encode(
                            y=alt.Y('Média', title='Valor'),
                            color='Sensor',
                            tooltip=['Data', 'Sensor', 'Média', 'Unidade']
                        )
                        
                        # Sombra (Min-Max)
                        band = base.mark_area(opacity=0.3).encode(
                            y='Mínima',
                            y2='Máxima',
                            color='Sensor'
                        )
                        
                        # Pontos de Máxima (Destaque visual)
                        points_max = base.mark_point(color='red', size=50, shape='triangle-up').encode(
                            y='Máxima',
                            color='Sensor',
                            tooltip=['Data', 'Sensor', 'Máxima']
                        )
                        
                        # Pontos de Mínima
                        points_min = base.mark_point(color='blue', size=50, shape='triangle-down').encode(
                            y='Mínima',
                            color='Sensor',
                            tooltip=['Data', 'Sensor', 'Mínima']
                        )

                        st.altair_chart((band + line + points_max + points_min).interactive(), use_container_width=True)

                    with tab2:
                        st.dataframe(df, use_container_width=True)
            else:
                st.error(f"Erro API: {res.text}")
        except Exception as e:
            st.error(f"Erro: {e}")
# ==========================================================
# 3. GERENCIAMENTO (CRUD)
# ==========================================================
elif choice == "Gerenciamento (CRUD)":
    st.title("📡 Gerenciamento de Dispositivos")
    if st.session_state["feedback_msg"]:
        if st.session_state["feedback_type"] == "success": st.success(st.session_state["feedback_msg"])
        elif st.session_state["feedback_type"] == "warning": st.warning(st.session_state["feedback_msg"])
        else: st.error(st.session_state["feedback_msg"])
        st.session_state["feedback_msg"] = None

    with st.form("cadastro_device"):
        st.write("### Novo Dispositivo")
        c1, c2 = st.columns(2)
        st.session_state.input_name = c1.text_input("Nome", placeholder="Ex: Arduino Bancada 1")
        st.session_state.input_slug = c2.text_input("Slug", placeholder="Ex: arduino-bancada-1")
        
        c3, c4 = st.columns(2)
        st.session_state.input_local = c3.text_input("Local", placeholder="Ex: Laboratório")
        
        st.form_submit_button("Cadastrar", on_click=submeter_formulario)

    st.divider()
    
    try:
        res = requests.get(f"{API_URL}/devices/")
        devices = res.json() if res.status_code == 200 else []
    except: devices = []
    
    if devices:
        cols = st.columns([0.5, 2, 2, 2, 1, 1.5])
        cols[0].write("**ID**")
        cols[1].write("**Nome**")
        cols[2].write("**Slug**")
        cols[3].write("**Local**")
        cols[4].write("**Status**")
        cols[5].write("**Ações**")
        st.write("---")
        for d in devices:
            if st.session_state["editing_id"] == d["id"]:
                with st.form(f"edt_{d['id']}"):
                    c = st.columns(3)
                    nn = c[0].text_input("Nome", d["name"])
                    ns = c[1].text_input("Slug", d["slug"])
                    nl = c[2].text_input("Local", d["location"])
                    if st.form_submit_button("Salvar"):
                        requests.patch(f"{API_URL}/devices/{d['id']}", json={"name": nn, "slug": ns, "location": nl})
                        st.session_state["editing_id"] = None; st.rerun()
            else:
                c = st.columns([0.5, 2, 2, 2, 1, 1.5])
                c[0].write(d['id']); c[1].write(d['name']); c[2].code(d['slug']); c[3].write(d['location'])
                c[4].write("🟢" if d.get('is_active') else "🔴")
                b1, b2 = c[5].columns(2)
                if b1.button("✏️", key=f"e_{d['id']}"): st.session_state["editing_id"] = d["id"]; st.rerun()
                if b2.button("🗑️", key=f"d_{d['id']}"): deletar_dispositivo(d['id']); st.rerun()
    else: st.info("Nenhum dispositivo.")