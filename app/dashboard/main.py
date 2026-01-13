import streamlit as st
import requests

API_URL = "http://backend:8000/api/v1"

st.set_page_config(page_title="Laboratório IoT", layout="centered")
st.title("🔌 Central de Comando IoT")

# --- 1. GERENCIAMENTO DE ESTADO ---
if "feedback_msg" not in st.session_state:
    st.session_state["feedback_msg"] = None
if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = None
if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None

# --- 2. FUNÇÕES DE CALLBACK (A Lógica separada da Tela) ---

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
            st.session_state["feedback_type"] = "warning" # Amarelo para chamar atenção
        else:
            st.session_state["feedback_msg"] = f"Erro ao arquivar: {response.text}"
            st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro de conexão: {e}"
        st.session_state["feedback_type"] = "error"

# --- 3. FEEDBACK VISUAL ---
if st.session_state["feedback_msg"]:
    if st.session_state["feedback_type"] == "success":
        st.success(st.session_state["feedback_msg"])
    elif st.session_state["feedback_type"] == "warning":
        st.warning(st.session_state["feedback_msg"])
    else:
        st.error(st.session_state["feedback_msg"])
    # Reset msg
    st.session_state["feedback_msg"] = None
    st.session_state["feedback_type"] = None

# --- 4. FORMULÁRIO ---
with st.form("cadastro_device"):
    st.write("### Cadastrar Novo Dispositivo")
    st.text_input("Nome do Dispositivo", key="input_name")
    st.text_input("Identificador (Slug)", key="input_slug")
    st.text_input("Localização", key="input_local")
    st.form_submit_button("Cadastrar", on_click=submeter_formulario)

st.divider()
st.subheader("📡 Dispositivos em Operação")

# --- 5. LISTAGEM ---
def carregar_dispositivos():
    try:
        response = requests.get(f"{API_URL}/devices/")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

devices = carregar_dispositivos()

if not devices:
    st.info("Nenhum dispositivo ativo encontrado.")
else:
    # Cabeçalho ajustado
    cols = st.columns([0.5, 2, 3.5, 1.5, 1, 2])
    cols[0].write("**ID**")
    cols[1].write("**Nome**")
    cols[2].write("**Slug**")
    cols[3].write("**Local**")
    cols[4].write("**Status**")
    cols[5].write("**Ações**")
    st.write("---")

    for device in devices:
        # --- MODO EDIÇÃO ---
        if st.session_state["editing_id"] == device["id"]:
            with st.container():
                st.info(f"✏️ Editando: {device['name']}")
                with st.form(key=f"edit_form_{device['id']}"):
                    c1, c2 = st.columns(2)
                    new_name = c1.text_input("Nome", value=device["name"])
                    new_slug = c2.text_input("Slug", value=device["slug"])
                    new_loc = st.text_input("Local", value=device["location"] or "")
                    
                    c_save, c_cancel = st.columns([1, 4])
                    # Note: Lógica de salvar pode virar callback tb no futuro se quiser
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

        # --- MODO LEITURA ---
        else:
            c1, c2, c3, c4, c5, c6 = st.columns([0.5, 2, 3.5, 1.5, 1, 2])
            c1.write(f"#{device['id']}")
            c2.write(device["name"])
            c3.code(device["slug"])
            c4.write(device["location"] or "-")
            c5.write("🟢" if device["is_active"] else "🔴")
            
            # Botões
            col_btn_edit, col_btn_del = c6.columns(2)
            
            with col_btn_edit:
                if st.button("✏️", key=f"btn_edit_{device['id']}"):
                    st.session_state["editing_id"] = device["id"]
                    st.rerun()
            
            with col_btn_del:
                st.button(
                    "🗑️", 
                    key=f"btn_del_{device['id']}",
                    on_click=deletar_dispositivo,
                    args=(device['id'],) 
                )
        
st.divider()
st.subheader("🌡️ Últimas Leituras Recebidas")

def carregar_medicoes():
    try:
        # Batendo no endpoint novo
        response = requests.get(f"{API_URL}/measurements/?limit=10")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

medicoes = carregar_medicoes()

if medicoes:
    # Mostra uma tabela simples
    st.dataframe(medicoes, use_container_width=True)
else:
    st.info("Aguardando dados dos sensores...")