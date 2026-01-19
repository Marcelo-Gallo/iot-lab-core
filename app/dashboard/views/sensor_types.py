import streamlit as st
import requests
from app.dashboard.utils import API_URL

def render_sensor_types_view():
    st.title("📏 Catálogo de Sensores")
    st.markdown("Defina aqui as grandezas físicas que o laboratório pode medir.")

    # CONTROLE DE ESTADO
    if "editing_sensor_id" not in st.session_state: 
        st.session_state["editing_sensor_id"] = None

    # FORMULÁRIO DE CADASTRO
    with st.expander("➕ Novo Tipo de Sensor", expanded=False):
        with st.form("new_sensor_type"):
            c1, c2 = st.columns([3, 1])
            name = c1.text_input("Nome da Grandeza", placeholder="Ex: Dióxido de Carbono")
            unit = c2.text_input("Unidade", placeholder="Ex: ppm")
            desc = st.text_input("Descrição (Opcional)", placeholder="Ex: Sensor MQ-135 para qualidade do ar")
            
            if st.form_submit_button("Cadastrar Grandeza"):
                if not name or not unit:
                    st.error("Nome e Unidade são obrigatórios.")
                else:
                    payload = {"name": name, "unit": unit, "description": desc}
                    try:
                        r = requests.post(f"{API_URL}/sensor-types/", json=payload)
                        if r.status_code == 200:
                            st.success(f"Sensacional! '{name}' agora faz parte do sistema.")
                            st.rerun()
                        else:
                            st.error(f"Erro: {r.json().get('detail', 'Erro desconhecido')}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")

    st.divider()

    # LISTAGEM
    try:
        res = requests.get(f"{API_URL}/sensor-types/")
        sensors = res.json() if res.status_code == 200 else []
        
        if not sensors:
            st.info("Nenhum tipo de sensor cadastrado.")
            return

        # Cabeçalho da Tabela
        col_h = st.columns([0.5, 2, 1, 3, 1.5])
        col_h[0].markdown("**ID**")
        col_h[1].markdown("**Nome**")
        col_h[2].markdown("**Unidade**")
        col_h[3].markdown("**Descrição / Status**") # Cabeçalho atualizado
        col_h[4].markdown("**Ações**")
        st.markdown("---")

        for s in sensors:
            # MODO EDIÇÃO
            if st.session_state["editing_sensor_id"] == s['id']:
                with st.container(border=True):
                    with st.form(f"edit_sensor_{s['id']}"):
                        cols = st.columns([2, 1, 3])
                        e_name = cols[0].text_input("Nome", value=s['name'])
                        e_unit = cols[1].text_input("Unidade", value=s['unit'])
                        e_desc = cols[2].text_input("Descrição", value=s.get('description', ''))
                        
                        b_salvar, b_cancelar = st.columns([1, 4])
                        
                        if b_salvar.form_submit_button("💾 Salvar"):
                            try:
                                payload = {"name": e_name, "unit": e_unit, "description": e_desc}
                                r = requests.patch(f"{API_URL}/sensor-types/{s['id']}", json=payload)
                                if r.status_code == 200:
                                    st.success("Atualizado!")
                                    st.session_state["editing_sensor_id"] = None
                                    st.rerun()
                                else:
                                    st.error(f"Erro: {r.text}")
                            except Exception as e:
                                st.error(f"Erro: {e}")

                        if b_cancelar.form_submit_button("Cancelar"):
                            st.session_state["editing_sensor_id"] = None
                            st.rerun()

            # MODO VISUALIZAÇÃO 
            else:
                c = st.columns([0.5, 2, 1, 3, 1.5])
                c[0].write(f"#{s['id']}")
                c[1].write(f"**{s['name']}**")
                c[2].code(s['unit'])

                is_active = s.get('is_active', True)
                status_icon = "🟢" if is_active else "🔴"
                c[3].write(f"{status_icon} {s.get('description', '-')}")
                
                b_edit, b_del = c[4].columns(2)
                
                if b_edit.button("✏️", key=f"btn_edit_{s['id']}"):
                    st.session_state["editing_sensor_id"] = s['id']
                    st.rerun()

                if is_active:
                    if b_del.button("⛔", key=f"btn_arch_{s['id']}", help="Arquivar (Desativar)"):
                        try:
                            r = requests.delete(f"{API_URL}/sensor-types/{s['id']}")
                            if r.status_code == 200:
                                st.toast(f"Sensor '{s['name']}' arquivado!")
                                st.rerun()
                            else:
                                st.error(f"Erro ao arquivar: {r.text}")
                        except Exception as e:
                            st.error(f"Erro: {e}")
                else:
                    if b_del.button("♻️", key=f"btn_rest_{s['id']}", help="Restaurar (Reativar)"):
                        try:
                            r = requests.patch(
                                f"{API_URL}/sensor-types/{s['id']}", 
                                json={"is_active": True}
                            )
                            if r.status_code == 200:
                                st.toast(f"Sensor '{s['name']}' restaurado com sucesso!")
                                st.rerun()
                            else:
                                st.error(f"Erro ao restaurar: {r.text}")
                        except Exception as e:
                            st.error(f"Erro: {e}")

            st.divider()

    except Exception as e:
        st.error(f"Erro ao carregar catálogo: {e}")