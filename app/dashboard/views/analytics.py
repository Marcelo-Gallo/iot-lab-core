import streamlit as st
import requests
import pandas as pd
import altair as alt
from app.dashboard.utils import API_URL, carregar_mapa_sensores, converter_para_local

def render_analytics_view():
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
                    
                    # KPIs por Sensor
                    st.divider()
                    st.write("### 🧠 Insights por Sensor")
                    sensores_unicos = df['Sensor'].unique()
                    cols_stats = st.columns(len(sensores_unicos))
                    
                    for i, sensor_nome in enumerate(sensores_unicos):
                        df_s = df[df['Sensor'] == sensor_nome]
                        media = df_s['Média'].mean()
                        unidade = df_s.iloc[0]['Unidade']
                        with cols_stats[i]:
                            st.markdown(f"**📡 {sensor_nome}**")
                            st.metric("Média", f"{media:.2f} {unidade}")

                    # Gráfico Altair
                    st.divider()
                    base = alt.Chart(df).encode(x=alt.X('Data', title='Tempo (BRT)', axis=alt.Axis(format='%H:%M')))
                    line = base.mark_line().encode(y=alt.Y('Média', title='Valor'), color='Sensor', tooltip=['Data', 'Sensor', 'Média'])
                    band = base.mark_area(opacity=0.3).encode(y='Mínima', y2='Máxima', color='Sensor')
                    
                    st.altair_chart((band + line).interactive(), use_container_width=True)
            else:
                st.error(f"Erro API: {res.text}")
        except Exception as e:
            st.error(f"Erro: {e}")