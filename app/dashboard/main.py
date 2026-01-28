import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)


import requests
from app.dashboard.utils import API_URL
from app.dashboard.views import sensor_types, devices, live, analytics

st.set_page_config(page_title="IoT Lab Dashboard", layout="wide")

if "token" not in st.session_state:
    st.session_state["token"] = None

def login_page():
    st.title("🔐 IoT Lab - Acesso Restrito")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                try:
                    response = requests.post(
                        f"{API_URL}/login/access-token",
                        data={"username": username, "password": password} # OAuth2 usa form data
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state["token"] = token_data["access_token"]
                        st.success("Login realizado!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                except Exception as e:
                    st.error(f"Erro de conexão: {e}")

def main_app():
    with st.sidebar:
        st.write(f"Logado como Admin")
        if st.button("Sair / Logout"):
            st.session_state["token"] = None
            st.rerun()
        st.divider()
    
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para:", ["Tempo Real", "Analítico", "Dispositivos", "Tipos de Sensor"])

    if page == "Tempo Real":
        live.render_live_dashboard()
    elif page == "Analítico":
        analytics.render_analytics_view()
    elif page == "Dispositivos":
        devices.render_devices_view()
    elif page == "Tipos de Sensor":
        sensor_types.render_sensor_types_view()

if st.session_state["token"]:
    main_app()
else:
    login_page()