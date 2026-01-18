import streamlit as st

# 1. GARANTIA DE LAYOUT WIDE
st.set_page_config(page_title="Histórico", layout="wide", page_icon="📊")

import pandas as pd
import altair as alt
from datetime import datetime, time as dt_time, date
import sys
import os

# Ajuste de path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.api_service import fetch_historical_data, carregar_mapa_sensores, get_active_devices_map

st.title("📊 Análise de Dados Históricos")

if "history_data" not in st.session_state: st.session_state.history_data = None

# Carrega mapas
sensor_map = carregar_mapa_sensores()
device_map, active_ids = get_active_devices_map()

with st.expander("🔎 Filtros", expanded=True):
    top_c1, top_c2 = st.columns([3, 1])
    
    with top_c2:
        # Checkbox para liberar os fantasmas
        show_archived = st.checkbox("Mostrar Arquivados", value=False)

    # --- LÓGICA VISUAL DA MARCAÇÃO 🔴 ---
    if show_archived:
        # Se for mostrar tudo, marcamos quem é inativo
        device_options = {}
        for k, v in device_map.items():
            nome_exibicao = v['name']
            if not v['active']:
                nome_exibicao += " 🔴 (Arq.)" # <--- MARCA VISUAL AQUI
            device_options[nome_exibicao] = k
    else:
        # Se for só ativos, lista limpa
        device_options = {v['name']: k for k, v in device_map.items() if v['active']}

    c1, c2, c3 = st.columns([1, 1, 1])
    date_range = c1.date_input("Período", (date.today(), date.today()))
    selected_names = c2.multiselect("Dispositivos", options=device_options.keys())
    limit = c3.number_input("Limite", value=1000, step=500)
    
    btn_search = st.button("Buscar", type="primary", use_container_width=True)

if btn_search:
    if len(date_range) != 2:
        st.warning("Selecione data início e fim.")
    else:
        try:
            start_dt = datetime.combine(date_range[0], dt_time.min)
            end_dt = datetime.combine(date_range[1], dt_time.max)
            
            params = {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "limit": limit
            }
            
            # Recupera IDs
            if selected_names:
                params["device_ids"] = [device_options[n] for n in selected_names]
            
            res = fetch_historical_data(params)
            
            if res.status_code == 200:
                data = res.json()
                if data:
                    processed = []
                    for row in data:
                        d_id = row['device_id']
                        
                        # Filtro de Inativos
                        if not show_archived and d_id not in active_ids: 
                            continue

                        s_id = row['sensor_type_id']
                        
                        # Pega dados do device
                        d_data = device_map.get(d_id, {'name': f"ID {d_id}", 'active': False})
                        d_name = d_data['name']
                        
                        # --- APLICA A MARCA NO GRÁFICO TAMBÉM ---
                        if not d_data['active']:
                             d_name += " 📦 (Arq.)"
                        # ----------------------------------------

                        sens_info = sensor_map.get(s_id, {'name': f"S{s_id}", 'unit': ''})
                        
                        processed.append({
                            "Data": row['created_at'],
                            "Valor": row['value'],
                            "Sensor": sens_info['name'],
                            "Unidade": sens_info['unit'],
                            "Device": d_name # O nome já vai com a bolinha vermelha
                        })
                    
                    if processed:
                        df = pd.DataFrame(processed)
                        df['Data'] = pd.to_datetime(df['Data'])
                        st.session_state.history_data = df
                        
                        msg_extra = ""
                        if len(data) >= limit: msg_extra = " (Limite atingido)"
                        st.success(f"{len(df)} registros carregados.{msg_extra}")
                    else:
                        st.warning("Dados filtrados.")
                else:
                    st.info("Nenhum dado encontrado no período.")
            else:
                st.error(f"Erro na API: {res.text}")
        except Exception as e:
            st.error(f"Erro: {e}")

# Renderização
if st.session_state.history_data is not None:
    df = st.session_state.history_data
    unique_sensors = df['Sensor'].unique()
    
    st.divider()
    for sensor in unique_sensors:
        df_s = df[df['Sensor'] == sensor]
        unit = df_s.iloc[0]['Unidade']
        st.markdown(f"### 📈 {sensor} ({unit})")
        
        # O campo 'Device' agora tem o emoji, então a legenda do gráfico separa as cores automaticamente
        c = alt.Chart(df_s).mark_line(point=True).encode(
            x=alt.X('Data', axis=alt.Axis(format='%d/%m %H:%M')),
            y=alt.Y('Valor', scale=alt.Scale(zero=False)),
            color=alt.Color('Device', legend=alt.Legend(title="Dispositivo")), 
            tooltip=['Data', 'Device', 'Valor']
        ).properties(height=300).interactive()
        st.altair_chart(c, use_container_width=True)
        st.divider()
    
    with st.expander("Dados Brutos"):
        st.dataframe(df, use_container_width=True)