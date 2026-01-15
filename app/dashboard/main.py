import streamlit as st
import requests
import pandas as pd
import asyncio
import websockets
import json
from datetime import datetime

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Laboratório IoT", layout="wide") 

API_URL = "http://backend:8000/api/v1"
WS_URL = "ws://backend:8000/api/v1/measurements/ws"

# --- 1. GERENCIAMENTO DE ESTADO (SESSION STATE) ---
if "feedback_msg" not in st.session_state:
    st.session_state["feedback_msg"] = None
if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = None
if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None
if "data_buffer" not in st.session_state:
    st.session_state.data_buffer = []

# --- 2. FUNÇÕES AUXILIARES (CRUD & LOGIC) ---
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

# --- 3. CORE DO WEBSOCKET (ASYNC) ---
async def listen_to_ws(kpi_container, chart_container, log_container, history_container):
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Não precisamos mais de toast aqui, pois o gráfico vivo já é o feedback
            
            latest_values = {1: 0.0, 2: 0.0}

            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                # Processamento de dados
                sensor_id = data['sensor_type_id']
                latest_values[sensor_id] = data['value']
                
                nome_sensor = "Desconhecido"
                if sensor_id == 1: nome_sensor = "Temperatura"
                elif sensor_id == 2: nome_sensor = "Umidade"
                else: nome_sensor = f"Sensor {sensor_id}"

                st.session_state.data_buffer.append({
                    "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                    "Valor": data["value"],
                    "Sensor": nome_sensor,
                    "Device ID": f"{data['device_id']}"
                })
                
                df = pd.DataFrame(st.session_state.data_buffer[-50:])
                
                # UI Update
                with kpi_container.container():
                    k1, k2, k3 = st.columns(3)
                    val_temp = latest_values.get(1, 0.0)
                    k1.metric("🌡️ Temperatura", f"{val_temp:.1f} °C")
                    val_hum = latest_values.get(2, 0.0)
                    k2.metric("💧 Umidade", f"{val_hum:.1f} %")
                    
                    hora_leitura = datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S")
                    k3.metric("⏱️ Monitoramento", hora_leitura, 
                             delta=f"Device ID: {data['device_id']}", delta_color="off")

                with chart_container:
                    st.line_chart(data=df, x="Hora", y="Valor", color="Sensor")

                with history_container:
                    st.dataframe(df[::-1][["Hora", "Sensor", "Valor", "Device ID"]], 
                               use_container_width=True, hide_index=True)
                    
                with log_container:
                    with st.expander("Debug: JSON Bruto"):
                        st.code(msg, language="json")

    except Exception as e:
        st.error(f"Conexão perdida ou interrompida: {e}")

# ==========================================================
# NAVEGAÇÃO LATERAL (SIDEBAR) 🧭
# ==========================================================
st.sidebar.title("🔌 IoT Lab Core")
st.sidebar.markdown("---")

# Menu de Opções
menu_options = ["Monitoramento (Live)", "Gerenciamento (CRUD)"]
choice = st.sidebar.radio("Navegação", menu_options)

st.sidebar.markdown("---")
st.sidebar.info("Sistema v2.0 | Websocket Ativo")

# ==========================================================
# PÁGINA 1: MONITORAMENTO (AUTO-START) 🚀
# ==========================================================
if choice == "Monitoramento (Live)":
    st.title("⚡ Monitoramento em Tempo Real")
    st.markdown("O sistema conecta automaticamente ao servidor. Aguarde os dados...")
    
    # Containers
    kpi_container = st.empty()
    chart_container = st.empty()
    st.write("### 📋 Histórico Recente (Ao Vivo)")
    history_container = st.empty()
    log_container = st.empty()
    
    # O SEGREDO: Chamada direta sem botão! 
    # O loop roda aqui e trava o script nesta página (que é o que queremos).
    # Se o usuário clicar no Sidebar, o Streamlit mata esse loop e vai para o else.
    asyncio.run(listen_to_ws(kpi_container, chart_container, log_container, history_container))

# ==========================================================
# PÁGINA 2: GERENCIAMENTO (CRUD) 🛠️
# ==========================================================
elif choice == "Gerenciamento (CRUD)":
    st.title("📡 Gerenciamento de Dispositivos")

    # Feedback Visual Global
    if st.session_state["feedback_msg"]:
        if st.session_state["feedback_type"] == "success":
            st.success(st.session_state["feedback_msg"])
        elif st.session_state["feedback_type"] == "warning":
            st.warning(st.session_state["feedback_msg"])
        else:
            st.error(st.session_state["feedback_msg"])
        st.session_state["feedback_msg"] = None

    # Formulário
    with st.form("cadastro_device"):
        st.write("### Novo Dispositivo")
        c1, c2 = st.columns(2)
        c1.text_input("Nome", key="input_name")
        c2.text_input("Slug (ID Único)", key="input_slug")
        st.text_input("Localização", key="input_local")
        st.form_submit_button("Cadastrar", on_click=submeter_formulario)

    st.divider()
    
    # Listagem
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
            # Lógica de Edição (Mantida igual)
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