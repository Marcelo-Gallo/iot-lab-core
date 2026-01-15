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

st.title("🔌 Central de Comando IoT")

# --- GERENCIAMENTO DE ESTADO (SESSION STATE) ---
if "feedback_msg" not in st.session_state:
    st.session_state["feedback_msg"] = None
if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = None
if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None
if "data_buffer" not in st.session_state:
    st.session_state.data_buffer = []

# --- FUNÇÕES DE CALLBACK (CRUD) ---
def submeter_formulario():
    """Callback para CADASTRAR"""
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
            # Limpa campos
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
    """Callback para DELETAR (Soft Delete)"""
    try:
        response = requests.delete(f"{API_URL}/devices/{device_id}")
        if response.status_code == 200:
            st.session_state["feedback_msg"] = "Dispositivo arquivado com sucesso."
            st.session_state["feedback_type"] = "warning"
        else:
            st.session_state["feedback_msg"] = f"Erro ao arquivar: {response.text}"
            st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro de conexão: {e}"
        st.session_state["feedback_type"] = "error"

# --- LÓGICA ASYNC (WEBSOCKET) ---
async def listen_to_ws(kpi_container, chart_container, log_container, history_container):
    try:
        async with websockets.connect(WS_URL) as websocket:
            st.toast("🟢 Conectado ao servidor WebSocket!")
            
            # Memória local para os KPIs
            latest_values = {1: 0.0, 2: 0.0}

            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                # Atualiza memória local
                sensor_id = data['sensor_type_id']
                latest_values[sensor_id] = data['value']
                
                # Define nome do sensor para o gráfico
                nome_sensor = "Desconhecido"
                if sensor_id == 1: nome_sensor = "Temperatura"
                elif sensor_id == 2: nome_sensor = "Umidade"
                else: nome_sensor = f"Sensor {sensor_id}"

                # Atualiza Buffer (Lista de histórico)
                st.session_state.data_buffer.append({
                    "Hora": datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S"),
                    "Valor": data["value"],
                    "Sensor": nome_sensor,
                    "Device ID": f"{data['device_id']}"
                })
                
                # Cria DataFrame (Últimos 50 pontos)
                df = pd.DataFrame(st.session_state.data_buffer[-50:])
                
                # ATUALIZA KPIs
                with kpi_container.container():
                    k1, k2, k3 = st.columns(3)
                    
                    val_temp = latest_values.get(1, 0.0)
                    k1.metric("🌡️ Temperatura", f"{val_temp:.1f} °C")
                    
                    val_hum = latest_values.get(2, 0.0)
                    k2.metric("💧 Umidade", f"{val_hum:.1f} %")
                    
                    hora_leitura = datetime.fromisoformat(data["created_at"]).strftime("%H:%M:%S")
                    k3.metric(
                        label="⏱️ Monitoramento",
                        value=hora_leitura,
                        delta=f"Fonte: Device {data['device_id']}",
                        delta_color="off"
                    )

                # ATUALIZA GRÁFICO
                with chart_container:
                    st.line_chart(data=df, x="Hora", y="Valor", color="Sensor")

                # 6. ATUALIZA TABELA AO VIVO
                with history_container:
                    # Inverte a ordem ([::-1]) para o mais novo ficar em cima
                    st.dataframe(
                        df[::-1][["Hora", "Sensor", "Valor", "Device ID"]], 
                        use_container_width=True,
                        hide_index=True
                    )
                    
                with log_container:
                    with st.expander("Ver JSON Bruto"):
                        st.code(msg, language="json")

    except Exception as e:
        st.error(f"Conexão perdida: {e}")

# ==========================================================
# LAYOUT PRINCIPAL COM ABAS
# ==========================================================
tab1, tab2 = st.tabs(["📡 Gerenciamento (CRUD)", "🌡️ Monitoramento (Live)"])

# ----------------------------------------------------------
# ABA 1: GERENCIAMENTO DE DISPOSITIVOS
# ----------------------------------------------------------
with tab1:
    # FEEDBACK VISUAL
    if st.session_state["feedback_msg"]:
        if st.session_state["feedback_type"] == "success":
            st.success(st.session_state["feedback_msg"])
        elif st.session_state["feedback_type"] == "warning":
            st.warning(st.session_state["feedback_msg"])
        else:
            st.error(st.session_state["feedback_msg"])
        st.session_state["feedback_msg"] = None
        st.session_state["feedback_type"] = None

    # FORMULÁRIO DE CADASTRO
    with st.form("cadastro_device"):
        st.write("### Cadastrar Novo Dispositivo")
        st.text_input("Nome do Dispositivo", key="input_name")
        st.text_input("Identificador (Slug)", key="input_slug")
        st.text_input("Localização", key="input_local")
        st.form_submit_button("Cadastrar", on_click=submeter_formulario)

    st.divider()
    st.subheader("📡 Dispositivos em Operação")

    # LISTAGEM
    def carregar_dispositivos():
        try:
            response = requests.get(f"{API_URL}/devices/")
            if response.status_code == 200: return response.json()
        except: pass
        return []

    devices = carregar_dispositivos()

    if not devices:
        st.info("Nenhum dispositivo ativo encontrado.")
    else:
        cols = st.columns([0.5, 2, 3.5, 1.5, 1, 2])
        cols[0].write("**ID**")
        cols[1].write("**Nome**")
        cols[2].write("**Slug**")
        cols[3].write("**Local**")
        cols[4].write("**Status**")
        cols[5].write("**Ações**")
        st.write("---")

        for device in devices:
            # MODO EDIÇÃO
            if st.session_state["editing_id"] == device["id"]:
                with st.container():
                    st.info(f"✏️ Editando: {device['name']}")
                    with st.form(key=f"edit_form_{device['id']}"):
                        c1, c2 = st.columns(2)
                        new_name = c1.text_input("Nome", value=device["name"])
                        new_slug = c2.text_input("Slug", value=device["slug"])
                        new_loc = st.text_input("Local", value=device["location"] or "")
                        
                        c_save, c_cancel = st.columns([1, 4])
                        save = c_save.form_submit_button("💾 Salvar") 
                        cancel = c_cancel.form_submit_button("❌ Cancelar")

                        if save:
                            payload = {"name": new_name, "slug": new_slug, "location": new_loc}
                            requests.patch(f"{API_URL}/devices/{device['id']}", json=payload)
                            st.session_state["feedback_msg"] = "Atualizado!"
                            st.session_state["feedback_type"] = "success"
                            st.session_state["editing_id"] = None
                            st.rerun()
                        if cancel:
                            st.session_state["editing_id"] = None
                            st.rerun()

            # MODO LEITURA
            else:
                c1, c2, c3, c4, c5, c6 = st.columns([0.5, 2, 3.5, 1.5, 1, 2])
                c1.write(f"#{device['id']}")
                c2.write(device["name"])
                c3.code(device["slug"])
                c4.write(device["location"] or "-")
                c5.write("🟢" if device["is_active"] else "🔴")
                
                col_btn_edit, col_btn_del = c6.columns(2)
                with col_btn_edit:
                    if st.button("✏️", key=f"btn_edit_{device['id']}"):
                        st.session_state["editing_id"] = device["id"]
                        st.rerun()
                with col_btn_del:
                    st.button("🗑️", key=f"btn_del_{device['id']}", on_click=deletar_dispositivo, args=(device['id'],))
            st.divider()
            

# ----------------------------------------------------------
# ABA 2: MONITORAMENTO EM TEMPO REAL
# ----------------------------------------------------------
with tab2:
    st.header("⚡ Monitoramento em Tempo Real")
    col_control, col_status = st.columns([1, 3])
    with col_control:
        start_btn = st.checkbox("🔴 Iniciar Conexão", value=False)
    
    # --- LAYOUT DOS ELEMENTOS ---
    kpi_container = st.empty()   # KPIs Fixos
    chart_container = st.empty() # Gráfico
    st.write("### 📋 Histórico Recente (Ao Vivo)")
    history_container = st.empty() # Tabela que se atualiza
    log_container = st.empty()   # JSON Debug

    if start_btn:
        asyncio.run(listen_to_ws(kpi_container, chart_container, log_container, history_container))