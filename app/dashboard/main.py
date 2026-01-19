import sys
import os
import time
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Imports das Views
from app.dashboard.views.live import render_live_view
from app.dashboard.views.analytics import render_analytics_view
from app.dashboard.views.devices import render_devices_view
from app.dashboard.views.sensor_types import render_sensor_types_view

# Configuração da Página
st.set_page_config(page_title="IoT Lab Core", layout="wide")

# Sidebar
st.sidebar.title("🔌 IoT Lab Core")
st.sidebar.markdown("---")

menu_options = {
    "Monitoramento (Live)": render_live_view,
    "Histórico (Analytics)": render_analytics_view,
    "Gerenciamento (CRUD)": render_devices_view,
    "Catálogo de Sensores": render_sensor_types_view,
}

choice = st.sidebar.radio("Navegação", list(menu_options.keys()))
st.sidebar.markdown("---")
st.sidebar.info("Sistema v3.2 | Modular Architecture")

root_container = st.empty()

root_container.empty()

time.sleep(0.05)

with root_container.container():
    if choice in menu_options:
        menu_options[choice]()