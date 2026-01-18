import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__)) # /code/app/dashboard
root_dir = os.path.abspath(os.path.join(current_dir, "../..")) # /code
if root_dir not in sys.path:
    sys.path.append(root_dir)

import streamlit as st
from app.dashboard.views.live import render_live_view
from app.dashboard.views.analytics import render_analytics_view
from app.dashboard.views.devices import render_devices_view

# Configuração da Página (Sempre a primeira linha)
st.set_page_config(page_title="IoT Lab Core", layout="wide")

# Sidebar de Navegação
st.sidebar.title("🔌 IoT Lab Core")
st.sidebar.markdown("---")

menu_options = {
    "Monitoramento (Live)": render_live_view,
    "Histórico (Analytics)": render_analytics_view,
    "Gerenciamento (CRUD)": render_devices_view
}

choice = st.sidebar.radio("Navegação", list(menu_options.keys()))
st.sidebar.markdown("---")
st.sidebar.info("Sistema v3.2 | Modular Architecture")

# Roteamento Dinâmico
if choice in menu_options:
    menu_options[choice]()