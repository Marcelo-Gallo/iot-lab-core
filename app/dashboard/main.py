import streamlit as st
import requests
import pandas as pd
import asyncio
import websockets
import json
from datetime import datetime, time, date
import altair as alt

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Laboratório IoT", layout="wide") 

API_URL = "http://backend:8000/api/v1"
WS_URL = "ws://backend:8000/api/v1/measurements/ws"

# --- GERENCIAMENTO DE ESTADO ---
if "feedback_msg" not in st.session_state:
    st.session_state["feedback_msg"] = None
if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = None
if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None
if "data_buffer" not in st.session_state:
    st.session_state.data_buffer = []
if "historico_data" not in st.session_state:
    st.session_state.historico_data = None
if "historico_count" not in st.session_state:
    st.session_state.historico_count = 0

# --- FUNÇÕES AUXILIARES ---
def carregar_mapa_sensores():
    try:
        response = requests.get(f"{API_URL}/sensor-types/") 
        if response.status_code == 404: 
             response = requests.get(f"{API_URL}/sensor_types/")

        if response.status_code == 200:
            tipos = response.json()
            return {
                t['id']: {'name': t['name'], 'unit': t['unit']} 
                for t in tipos
            }
    except:
        pass
    return {1: {'name': "Temperatura", 'unit': "°C"}, 2: {'name': "Umidade", 'unit': "%"}}

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
            st.session_state["feedback_msg"] = f"Dispositivo '{payload['name']}' cadastrado!"
            st.session_state["feedback_type"] = "success"
            st.session_state.input_name = ""
            st.session_state.input_slug = ""
            st.session_state.input_local = ""
        else:
            err = response.json().get('detail', 'Erro')
            st.session_state["feedback_msg"] = f"Erro: {err}"
            st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro Conexão: {e}"
        st.session_state["feedback_type"] = "error"

def deletar_dispositivo(device_id):
    try:
        response = requests.delete(f"{API_URL}/devices/{device_id}")
        if response.status_code == 200:
            st.session_state["feedback_msg"] = "Dispositivo arquivado."
            st.session_state["feedback_type"] = "warning"
        else:
            st.session_state["feedback_msg"] = f"Erro: {response.text}"
            st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro: {e}"
        st.session_state["feedback_type"] = "error"

# --- CORE DO WEBSOCKET ---
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
                        info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                        st.session_state.data_buffer.append({
                            "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                            "Valor": data["value"],
                            "Sensor": info['name'],
                            "Device ID": f"{data['device_id']}",
                            "Unidade": info['unit']
                        })
            except Exception as e:
                print(f"Erro no backfill: {e}") 

        async with websockets.connect(WS_URL) as websocket:
            latest_values = {}
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                s_id = data['sensor_type_id']
                latest_values[s_id] = data['value']
                info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})

                st.session_state.data_buffer.append({
                    "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
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
                    
                    hora = datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S")
                    cols[-1].metric("⏱️ Monitoramento", hora, delta=f"ID: {data['device_id']}", delta_color="off")

                with chart_container:
                    st.line_chart(data=df, x="Hora", y="Valor", color="Sensor")

                with history_container:
                    st.dataframe(df[::-1][["Hora", "Sensor", "Valor", "Device ID"]], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Conexão perdida: {e}")

# ==========================================================
# NAVEGAÇÃO
# ==========================================================
st.sidebar.title("🔌 IoT Lab Core")
st.sidebar.markdown("---")
menu_options = ["Monitoramento (Live)", "Histórico (Análise)", "Gerenciamento (CRUD)"]
choice = st.sidebar.radio("Navegação", menu_options)
st.sidebar.markdown("---")
st.sidebar.info("Sistema v2.6 | Session State & Cards")

# ==========================================================
# MONITORAMENTO
# ==========================================================
if choice == "Monitoramento (Live)":
    st.title("⚡ Monitoramento em Tempo Real")
    kpi_container = st.empty()
    chart_container = st.empty()
    st.write("### 📋 Buffer Recente")
    history_container = st.empty()
    log_container = st.empty()
    asyncio.run(listen_to_ws(kpi_container, chart_container, log_container, history_container))

# ==========================================================
# HISTÓRICO (ANÁLISE)
# ==========================================================
elif choice == "Histórico (Análise)":
    st.title("📊 Análise de Dados Históricos")
    st.markdown("Consulte o banco de dados completo e exporte para CSV.")

    with st.expander("🔎 Filtros de Pesquisa", expanded=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            today = date.today()
            date_range = st.date_input("Selecione o Período", (today, today))
        with c2:
            limit_val = st.number_input("Limite de Registros", min_value=100, value=1000, step=100)
        with c3:
            st.write("") 
            st.write("") 
            search_btn = st.button("Buscar Dados 🔎", type="primary", use_container_width=True)

    # LÓGICA DE BUSCA (Salva no Session State)
    if search_btn:
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)
            
            try:
                sensor_map = carregar_mapa_sensores()
                params = {"start_date": start_dt.isoformat(), "end_date": end_dt.isoformat(), "limit": limit_val}
                
                res_measurements = requests.get(f"{API_URL}/measurements/", params=params)
                res_devices = requests.get(f"{API_URL}/devices/")
                
                if res_measurements.status_code == 200 and res_devices.status_code == 200:
                    data = res_measurements.json()
                    devices_list = res_devices.json()
                    
                    device_map_name = {d['id']: d['name'] for d in devices_list}
                    device_map_loc = {d['id']: d['location'] for d in devices_list}

                    if data:
                        processed_data = []
                        for item in data:
                            dev_id = item['device_id']
                            s_id = item['sensor_type_id']
                            info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                            dev_name = device_map_name.get(dev_id, "Desconhecido")
                            
                            processed_data.append({
                                "Data/Hora": item['created_at'],
                                "Sensor": info['name'],
                                "Unidade": info['unit'],
                                "Valor": item['value'],
                                "Device ID": dev_id,
                                "Dispositivo": dev_name,
                                "Localização": device_map_loc.get(dev_id, "Não definido"),
                                "Legenda": f"{dev_name} ({info['name']})"
                            })
                        
                        df = pd.DataFrame(processed_data)
                        df['Data/Hora'] = pd.to_datetime(df['Data/Hora'])
                        
                        st.session_state.historico_data = df
                        st.session_state.historico_count = len(df)
                        st.success(f"Busca realizada! {len(df)} registros encontrados.")
                    else:
                        st.warning("Nenhum dado encontrado neste período.")
                        st.session_state.historico_data = None
                else:
                    st.error("Erro na API.")
            except Exception as e:
                st.error(f"Erro: {e}")

    # RENDERIZAÇÃO
    if st.session_state.historico_data is not None:
        df = st.session_state.historico_data
        count = st.session_state.historico_count
        
        # --- CARDS DE ESTATÍSTICA (INSIGHTS AUTOMÁTICOS) ---
        st.divider()
        st.write("### 🧠 Insights por Sensor")
        
        sensores_unicos = df['Sensor'].unique()
        
        # Cria colunas dinâmicas pra cada sensor
        cols_stats = st.columns(len(sensores_unicos))
        
        for i, sensor_nome in enumerate(sensores_unicos):
            df_s = df[df['Sensor'] == sensor_nome]
            if not df_s.empty:
                media = df_s["Valor"].mean()
                max_val = df_s["Valor"].max()
                min_val = df_s["Valor"].min()
                unidade = df_s.iloc[0]['Unidade']
                
                # Card Estilizado
                with cols_stats[i]:
                    st.markdown(f"**📡 {sensor_nome}**")
                    st.metric("Média", f"{media:.2f} {unidade}")
                    st.caption(f"Max: {max_val} | Min: {min_val}")
        st.divider()
        # ---------------------------------------------------

        LIMITE_GRAFICO = 5000
        show_chart = True
        if count > LIMITE_GRAFICO:
            st.warning(f"⚠️ Volume alto ({count}). Gráfico desativado.")
            tab_dados = st.container()
            show_chart = False
        else:
            tab_graf, tab_dados = st.tabs(["📈 Gráfico", "📋 Tabela & Exportação"])

        if show_chart:
            with tab_graf:
                chart = alt.Chart(df).mark_line(point=True).encode(
                    x=alt.X('Data/Hora', axis=alt.Axis(format='%d/%m %H:%M', title='Tempo')),
                    y=alt.Y('Valor', title='Leitura'),
                    color=alt.Color('Legenda', legend=alt.Legend(orient='bottom', columns=3, labelLimit=0)),
                    tooltip=['Data/Hora', 'Dispositivo', 'Sensor', 'Valor', 'Unidade']
                ).properties(height=400).interactive()
                st.altair_chart(chart, use_container_width=True)
        
        with tab_dados:
            st.dataframe(df[["Data/Hora", "Dispositivo", "Sensor", "Valor", "Unidade", "Localização"]], use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV", csv, "relatorio.csv", "text/csv")

# ==========================================================
# GERENCIAMENTO (CRUD)
# ==========================================================
elif choice == "Gerenciamento (CRUD)":
    st.title("📡 Gerenciamento de Dispositivos")
    if st.session_state["feedback_msg"]:
        if st.session_state["feedback_type"] == "success": st.success(st.session_state["feedback_msg"])
        elif st.session_state["feedback_type"] == "warning": st.warning(st.session_state["feedback_msg"])
        else: st.error(st.session_state["feedback_msg"])
        st.session_state["feedback_msg"] = None

    with st.form("cadastro"):
        c1, c2 = st.columns(2)
        st.session_state.input_name = c1.text_input("Nome")
        st.session_state.input_slug = c2.text_input("Slug")
        st.session_state.input_local = st.text_input("Local")
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