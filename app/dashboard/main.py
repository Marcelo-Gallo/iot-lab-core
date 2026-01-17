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

# --- 1. GERENCIAMENTO DE ESTADO ---
if "feedback_msg" not in st.session_state:
    st.session_state["feedback_msg"] = None
if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = None
if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None
if "data_buffer" not in st.session_state:
    st.session_state.data_buffer = []

# --- 2. FUNÇÕES AUXILIARES ---
def carregar_mapa_sensores():
    """
    Busca os tipos de sensores no backend e cria um mapa rico.
    Retorna: {
        1: {'name': 'Temperatura', 'unit': '°C'}, 
        2: {'name': 'Umidade', 'unit': '%'}
    }
    """
    try:
        response = requests.get(f"{API_URL}/sensor-types/") # Ajustei rota para plural correto se necessário
        # Fallback caso a rota seja /sensor_types/ ou /sensor-types/ (verifique no seu backend)
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
    
    # Fallback seguro apenas para não quebrar se API cair
    return {
        1: {'name': "Temperatura", 'unit': "°C"}, 
        2: {'name': "Umidade", 'unit': "%"}
    }

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

# --- 3. CORE DO WEBSOCKET ---
async def listen_to_ws(kpi_container, chart_container, log_container, history_container):
    try:
        # Carrega o mapa rico (Nome + Unidade)
        sensor_map = carregar_mapa_sensores()
        
        # --- BACKFILL ---
        if not st.session_state.data_buffer:
            try:
                res = requests.get(f"{API_URL}/measurements/?limit=50")
                if res.status_code == 200:
                    history_data = res.json()
                    for data in reversed(history_data):
                        s_id = data['sensor_type_id']
                        
                        # Recupera dados do mapa ou usa fallback genérico
                        info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                        nome_completo = f"{info['name']}" # Ex: Temperatura

                        st.session_state.data_buffer.append({
                            "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                            "Valor": data["value"],
                            "Sensor": nome_completo,
                            "Device ID": f"{data['device_id']}",
                            "Unidade": info['unit'] # Guardamos a unidade para uso futuro se precisar
                        })
            except Exception as e:
                print(f"Erro no backfill: {e}") 
        # ----------------

        async with websockets.connect(WS_URL) as websocket:
            latest_values = {} # Guarda último valor {id: valor}

            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                s_id = data['sensor_type_id']
                latest_values[s_id] = data['value']
                
                # Usa o mesmo mapa para garantir consistência
                info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                nome_completo = f"{info['name']}"

                st.session_state.data_buffer.append({
                    "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                    "Valor": data["value"],
                    "Sensor": nome_completo,
                    "Device ID": f"{data['device_id']}",
                    "Unidade": info['unit']
                })
                
                if len(st.session_state.data_buffer) > 50:
                    st.session_state.data_buffer.pop(0)

                df = pd.DataFrame(st.session_state.data_buffer)
                
                # --- ATUALIZAÇÃO DOS KPIS (100% AGNÓSTICA) ---
                with kpi_container.container():
                    qtd_sensores = len(latest_values)
                    # Cria colunas dinâmicas (+1 para o Relógio)
                    cols = st.columns(qtd_sensores + 1)
                    
                    # Itera sobre os sensores ativos
                    for i, (sens_id, valor) in enumerate(latest_values.items()):
                        # Busca info no mapa (Nome e Unidade)
                        info = sensor_map.get(sens_id, {'name': f"Sensor {sens_id}", 'unit': ''})
                        
                        # Renderiza KPI sem IFs mágicos
                        cols[i].metric(
                            label=f"📡 {info['name']}", 
                            value=f"{valor:.1f} {info['unit']}" # Unidade vem do banco!
                        )
                    
                    # Relógio (Sempre na última coluna)
                    hora_leitura = datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S")
                    cols[-1].metric("⏱️ Monitoramento", hora_leitura, delta=f"ID: {data['device_id']}", delta_color="off")

                with chart_container:
                    st.line_chart(data=df, x="Hora", y="Valor", color="Sensor")

                with history_container:
                    st.dataframe(df[::-1][["Hora", "Sensor", "Valor", "Device ID"]], 
                               use_container_width=True, hide_index=True)
                    
                with log_container:
                    with st.expander("Debug: JSON Bruto"):
                        st.code(msg, language="json")

    except Exception as e:
        st.error(f"Conexão perdida: {e}")

# ==========================================================
# NAVEGAÇÃO LATERAL
# ==========================================================
st.sidebar.title("🔌 IoT Lab Core")
st.sidebar.markdown("---")

menu_options = ["Monitoramento (Live)", "Histórico (Análise)", "Gerenciamento (CRUD)"]
choice = st.sidebar.radio("Navegação", menu_options)

st.sidebar.markdown("---")
st.sidebar.info("Sistema v2.4 | Unit Aware")

# ==========================================================
# PÁGINA 1: MONITORAMENTO (LIVE)
# ==========================================================
if choice == "Monitoramento (Live)":
    st.title("⚡ Monitoramento em Tempo Real")
    st.markdown("Conectado via WebSocket. Visualizando dados recentes (Buffer).")
    
    kpi_container = st.empty()
    chart_container = st.empty()
    st.write("### 📋 Buffer Recente")
    history_container = st.empty()
    log_container = st.empty()
    
    asyncio.run(listen_to_ws(kpi_container, chart_container, log_container, history_container))

# ==========================================================
# PÁGINA 2: HISTÓRICO (ANÁLISE DE DADOS)
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

    if search_btn:
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)
            
            try:
                # Carrega mapas para enriquecimento
                sensor_map = carregar_mapa_sensores()
                
                params = {
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat(),
                    "limit": limit_val
                }
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
                            
                            # Recupera Nome e Unidade
                            info = sensor_map.get(s_id, {'name': f"Sensor {s_id}", 'unit': ''})
                            dev_name = device_map_name.get(dev_id, "Desconhecido")
                            
                            # Legenda com Unidade! Ex: "Estufa 1 (Temperatura - °C)"
                            legenda_grafico = f"{dev_name} ({info['name']})" 

                            processed_data.append({
                                "Data/Hora": item['created_at'],
                                "Sensor": info['name'],
                                "Unidade": info['unit'], # Nova coluna para tabela
                                "Valor": item['value'],
                                "Device ID": dev_id,
                                "Dispositivo": dev_name,
                                "Localização": device_map_loc.get(dev_id, "Não definido"),
                                "Legenda": legenda_grafico
                            })
                        
                        df_hist = pd.DataFrame(processed_data)
                        df_hist['Data/Hora'] = pd.to_datetime(df_hist['Data/Hora'])
                        
                        count = len(df_hist)

                        st.divider()
                        st.write("### 📊 Resumo do Período")
                        k1, k2, k3, k4 = st.columns(4)
                        k1.metric("Média Geral", f"{df_hist['Valor'].mean():.2f}")
                        k2.metric("Pico Máximo", f"{df_hist['Valor'].max():.2f}")
                        k3.metric("Mínima", f"{df_hist['Valor'].min():.2f}")
                        k4.metric("Total de Leituras", count)
                        st.divider()
                        
                        LIMITE_GRAFICO = 5000
                        if count > LIMITE_GRAFICO:
                            st.warning(f"⚠️ Volume alto de dados ({count}). Gráfico desativado.")
                            tab_dados = st.container()
                            show_chart = False
                        else:
                            st.success(f"Encontrados {count} registros.")
                            tab_graf, tab_dados = st.tabs(["📈 Gráfico", "📋 Tabela & Exportação"])
                            show_chart = True

                        if show_chart:
                            with tab_graf:
                                chart = alt.Chart(df_hist).mark_line(point=True).encode(
                                    x=alt.X('Data/Hora', format='%d/%m %H:%M', title='Tempo'),
                                    y=alt.Y('Valor', title='Leitura'),
                                    color=alt.Color('Legenda', legend=alt.Legend(orient='bottom', columns=3, labelLimit=0)),
                                    # Tooltip agora mostra a unidade correta
                                    tooltip=['Data/Hora', 'Dispositivo', 'Sensor', 'Valor', 'Unidade']
                                ).properties(height=400).interactive()
                                st.altair_chart(chart, use_container_width=True)
                            
                        with tab_dados:
                            # Adicionei a coluna "Unidade" na tabela também
                            colunas = ["Data/Hora", "Dispositivo", "Sensor", "Valor", "Unidade", "Localização"]
                            st.dataframe(df_hist[colunas], use_container_width=True)
                            csv = df_hist.to_csv(index=False).encode('utf-8')
                            st.download_button("📥 Baixar CSV", csv, "relatorio.csv", "text/csv")
                    else:
                        st.warning("Nenhum dado encontrado.")
                else:
                    st.error("Erro na API.")
            except Exception as e:
                st.error(f"Erro: {e}")
        else:
            st.warning("Selecione data início e fim.")

# ==========================================================
# PÁGINA 3: GERENCIAMENTO (CRUD)
# ==========================================================
elif choice == "Gerenciamento (CRUD)":
    st.title("📡 Gerenciamento de Dispositivos")

    if st.session_state["feedback_msg"]:
        if st.session_state["feedback_type"] == "success":
            st.success(st.session_state["feedback_msg"])
        elif st.session_state["feedback_type"] == "warning":
            st.warning(st.session_state["feedback_msg"])
        else:
            st.error(st.session_state["feedback_msg"])
        st.session_state["feedback_msg"] = None

    with st.form("cadastro_device"):
        st.write("### Novo Dispositivo")
        c1, c2 = st.columns(2)
        c1.text_input("Nome", key="input_name")
        c2.text_input("Slug (ID Único)", key="input_slug")
        st.text_input("Localização", key="input_local")
        st.form_submit_button("Cadastrar", on_click=submeter_formulario)

    st.divider()
    st.subheader("Dispositivos Ativos")
    
    def carregar_dispositivos():
        try:
            res = requests.get(f"{API_URL}/devices/")
            if res.status_code == 200: return res.json()
        except: pass
        return []

    devices = carregar_dispositivos()
    
    if devices:
        cols = st.columns([0.5, 2, 2, 2, 1, 1.5])
        cols[0].write("**ID**")
        cols[1].write("**Nome**")
        cols[2].write("**Slug**")
        cols[3].write("**Local**")
        cols[4].write("**Status**")
        cols[5].write("**Ações**")
        st.write("---")

        for device in devices:
            if st.session_state["editing_id"] == device["id"]:
                with st.container():
                    with st.form(key=f"edit_{device['id']}"):
                        col_edit = st.columns(3)
                        n_name = col_edit[0].text_input("Nome", device["name"])
                        n_slug = col_edit[1].text_input("Slug", device["slug"])
                        n_loc = col_edit[2].text_input("Local", device["location"] or "")
                        if st.form_submit_button("💾 Salvar"):
                            requests.patch(f"{API_URL}/devices/{device['id']}", 
                                         json={"name": n_name, "slug": n_slug, "location": n_loc})
                            st.session_state["editing_id"] = None
                            st.session_state["feedback_msg"] = "Editado!"
                            st.session_state["feedback_type"] = "success"
                            st.rerun()
            else:
                c = st.columns([0.5, 2, 2, 2, 1, 1.5])
                c[0].write(device['id'])
                c[1].write(device['name'])
                c[2].code(device['slug'])
                c[3].write(device['location'])
                c[4].write("✅")
                b1, b2 = c[5].columns(2)
                if b1.button("✏️", key=f"e_{device['id']}"):
                    st.session_state["editing_id"] = device["id"]
                    st.rerun()
                if b2.button("🗑️", key=f"d_{device['id']}"):
                    deletar_dispositivo(device['id'])
                    st.rerun()
    else:
        st.info("Nenhum dispositivo encontrado.")