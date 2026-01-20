import streamlit as st
import requests
import pandas as pd
import altair as alt
import math
from app.dashboard.utils import API_URL, carregar_mapa_sensores, converter_para_local

def render_analytics_view():
    st.title("📊 Análise Inteligente de Dados")
    
    # --- PREPARAÇÃO DE SEGURANÇA ---
    # Recupera o token para usar nas chamadas de API
    token = st.session_state.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # --- BARRA DE CONFIGURAÇÃO ---
    with st.expander("⚙️ Configuração da Análise", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            periodo = st.selectbox(
                "Janela de Tempo", 
                ["1h", "1d", "1w", "1m"], 
                format_func=lambda x: {"1h":"Última Hora", "1d":"Últimas 24h", "1w":"Última Semana", "1m":"Último Mês"}[x]
            )
        with c2:
            # Seleção inteligente do bucket padrão
            default_idx = 0 if periodo == '1h' else 1 if periodo == '1d' else 2
            bucket = st.selectbox(
                "Agrupamento (Resolução)", 
                ["minute", "hour", "day"], 
                index=default_idx, 
                format_func=lambda x: {"minute":"Minuto a Minuto", "hour":"Hora em Hora", "day":"Diário"}[x]
            )
        with c3:
            st.write(""); st.write("") # Espaçamento para alinhar o botão
            btn_update = st.button("🔄 Gerar Relatório", type="primary", use_container_width=True)

    # --- PROCESSAMENTO ---
    if btn_update:
        try:
            # Busca metadados dos sensores (GET público ou protegido)
            # Nota: Se o GET /sensor-types for protegido, carregar_mapa_sensores precisaria ser atualizado em utils.py
            sensor_map = carregar_mapa_sensores()
            
            # Busca dados analíticos do backend
            params = {"period": periodo, "bucket_size": bucket}
            
            with st.spinner("Processando estatísticas..."):
                # INJEÇÃO DO TOKEN AQUI
                res = requests.get(
                    f"{API_URL}/measurements/analytics/", 
                    params=params, 
                    headers=headers # <--- Autenticação
                )
            
            # Tratamento de Erros de Autenticação
            if res.status_code == 401:
                st.error("🔒 Sessão expirada. Faça login novamente.")
                return

            if res.status_code == 200:
                data = res.json()
                if not data:
                    st.warning("📭 Nenhum dado encontrado para este período.")
                    return

                # Processa JSON para DataFrame
                rows = []
                for item in data:
                    s_id = item['sensor_type_id']
                    # Usa o mapa para pegar nome amigável ou fallback para o ID
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
                
                # --- RENDERIZAÇÃO EM CARDS ---
                st.divider()
                st.subheader("🧠 Insights por Tipo de Sensor")
                
                if 'Sensor' in df.columns:
                    sensores_unicos = df['Sensor'].unique()
                    
                    # Lógica de Grid Responsivo (2 cards por linha)
                    cols_per_row = 2
                    rows_count = math.ceil(len(sensores_unicos) / cols_per_row)

                    for r in range(rows_count):
                        cols = st.columns(cols_per_row)
                        for c in range(cols_per_row):
                            idx = r * cols_per_row + c
                            
                            if idx < len(sensores_unicos):
                                sensor_nome = sensores_unicos[idx]
                                
                                # Filtra dados APENAS deste sensor
                                df_s = df[df['Sensor'] == sensor_nome].sort_values("Data")
                                unidade = df_s.iloc[0]['Unidade']
                                
                                # Estatísticas Gerais do Período
                                avg_total = df_s['Média'].mean()
                                min_total = df_s['Mínima'].min()
                                max_total = df_s['Máxima'].max()
                                
                                with cols[c]:
                                    with st.container(border=True):
                                        # Cabeçalho do Card
                                        st.markdown(f"### 📡 {sensor_nome}")
                                        
                                        # KPIs Principais
                                        k1, k2, k3 = st.columns(3)
                                        k1.metric("Média Global", f"{avg_total:.1f} {unidade}")
                                        k2.metric("Mínima Abs", f"{min_total:.1f} {unidade}")
                                        k3.metric("Máxima Abs", f"{max_total:.1f} {unidade}")
                                        
                                        st.divider()
                                        
                                        # Gráfico de Área (Min-Max) com Linha de Média
                                        base = alt.Chart(df_s).encode(
                                            x=alt.X('Data', title=None, axis=alt.Axis(format='%H:%M'))
                                        )
                                        
                                        # Linha da Média
                                        line = base.mark_line(color='#4E8CFF').encode(
                                            y=alt.Y('Média', title=f"Valor ({unidade})", scale=alt.Scale(zero=False)),
                                            tooltip=['Data', 'Média', 'Mínima', 'Máxima', 'Amostras']
                                        )
                                        
                                        # Faixa de Variação (Min até Max)
                                        band = base.mark_area(opacity=0.3, color='#4E8CFF').encode(
                                            y='Mínima',
                                            y2='Máxima'
                                        )
                                        
                                        st.altair_chart((band + line).interactive(), use_container_width=True)
                else:
                    st.error("Erro na estrutura dos dados recebidos.")

            else:
                st.error(f"Erro ao conectar na API: {res.text}")
        except Exception as e:
            st.error(f"Erro interno: {e}")