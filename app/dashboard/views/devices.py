import streamlit as st
import requests
from app.dashboard.utils import API_URL

# --- FUNÇÃO CALLBACK (Executa ANTES de desenhar a tela) ---
def alternar_status_device(device_id, status_atual):
    novo_status = not status_atual
    try:
        r = requests.patch(f"{API_URL}/devices/{device_id}", json={"is_active": novo_status})
        if r.status_code == 200:
            msg = "Dispositivo ativado!" if novo_status else "Dispositivo arquivado."
            st.session_state["feedback_msg"] = msg
            st.session_state["feedback_type"] = "success" if novo_status else "warning"
        else:
            st.session_state["feedback_msg"] = f"Erro API: {r.text}"
            st.session_state["feedback_type"] = "error"
    except Exception as e:
        st.session_state["feedback_msg"] = f"Erro Conexão: {e}"
        st.session_state["feedback_type"] = "error"

def render_devices_view():
    st.title("📡 Gerenciamento de Dispositivos")
    
    # --- 1. GERENCIAMENTO DE ESTADO ---
    if "editing_id" not in st.session_state: st.session_state["editing_id"] = None
    if "configuring_id" not in st.session_state: st.session_state["configuring_id"] = None
    if "feedback_msg" not in st.session_state: st.session_state["feedback_msg"] = None
    if "feedback_type" not in st.session_state: st.session_state["feedback_type"] = None

    # Exibe mensagens de feedback (Toast ou Alert)
    if st.session_state["feedback_msg"]:
        tipo = st.session_state["feedback_type"]
        msg = st.session_state["feedback_msg"]
        if tipo == "success": st.success(msg)
        elif tipo == "warning": st.warning(msg)
        else: st.error(msg)
        # Limpa após exibir para não ficar persistente
        st.session_state["feedback_msg"] = None

    # --- 2. CADASTRO ---
    with st.form("cadastro_device"):
        st.write("### Novo Dispositivo")
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome", placeholder="Ex: Arduino Lab 1")
        slug = c2.text_input("Slug (ID Único)", placeholder="Ex: arduino-lab-1")
        c3, c4 = st.columns(2)
        local = c3.text_input("Localização", placeholder="Ex: Bancada A")
        
        if st.form_submit_button("Cadastrar Dispositivo"):
            payload = {"name": name, "slug": slug, "location": local, "is_active": True}
            try:
                r = requests.post(f"{API_URL}/devices/", json=payload)
                if r.status_code == 200:
                    st.success(f"Dispositivo '{name}' criado!")
                    st.rerun()
                else:
                    st.error(f"Erro: {r.json().get('detail', 'Desconhecido')}")
            except Exception as e:
                st.error(f"Erro Conexão: {e}")

    st.divider()
    
    # --- 3. LISTAGEM ---
    try:
        # Busca dados (Agora já virão atualizados por causa do Callback)
        res = requests.get(f"{API_URL}/devices/")
        devices = res.json() if res.status_code == 200 else []
        
        # Busca Tipos de Sensores
        res_types = requests.get(f"{API_URL}/sensor-types/")
        sensor_types = res_types.json() if res_types.status_code == 200 else []
        sensor_options = {s['name']: s['id'] for s in sensor_types}
        
        if not devices:
            st.info("Nenhum dispositivo cadastrado.")
        else:
            mostrar_arquivados = st.checkbox("Mostrar Dispositivos Arquivados", value=True)
            devices_filtrados = [d for d in devices if d['is_active'] or mostrar_arquivados]

            cols = st.columns([0.5, 2, 2, 1.5, 1, 2.5])
            cols[0].markdown("**ID**")
            cols[1].markdown("**Nome**")
            cols[2].markdown("**Slug**")
            cols[3].markdown("**Local**")
            cols[4].markdown("**Status**")
            cols[5].markdown("**Ações**")
            st.markdown("---")

            for d in devices_filtrados:
                
                # --- MODO 1: CONFIGURAÇÃO DE SENSORES (NOVO) ---
                if st.session_state["configuring_id"] == d["id"]:
                    with st.container(border=True):
                        st.info(f"⚙️ Configurando Sensores: **{d['name']}**")
                        
                        # 1. Busca sensores atuais deste device
                        try:
                            r_curr = requests.get(f"{API_URL}/devices/{d['id']}/sensors")
                            current_ids = r_curr.json() if r_curr.status_code == 200 else []
                        except: current_ids = []
                        
                        # Converte IDs para Nomes para o widget
                        default_names = [name for name, sid in sensor_options.items() if sid in current_ids]
                        
                        with st.form(f"config_sensors_{d['id']}"):
                            selected_names = st.multiselect(
                                "Quais sensores este dispositivo possui?",
                                options=list(sensor_options.keys()),
                                default=default_names
                            )
                            
                            c_save, c_canc = st.columns([1, 4])
                            if c_save.form_submit_button("💾 Salvar Vínculo"):
                                # Converte Nomes de volta para IDs
                                new_ids = [sensor_options[name] for name in selected_names]
                                try:
                                    r_up = requests.post(
                                        f"{API_URL}/devices/{d['id']}/sensors", 
                                        json={"sensor_ids": new_ids}
                                    )
                                    if r_up.status_code == 200:
                                        st.session_state["feedback_msg"] = "Vínculos atualizados com sucesso!"
                                        st.session_state["feedback_type"] = "success"
                                        st.session_state["configuring_id"] = None
                                        st.rerun()
                                    else:
                                        st.error(f"Erro: {r_up.text}")
                                except Exception as e:
                                    st.error(f"Erro: {e}")

                            if c_canc.form_submit_button("Cancelar"):
                                st.session_state["configuring_id"] = None
                                st.rerun()

                if st.session_state["configuring_id"] == d["id"]:
                    with st.container(border=True):
                        st.info(f"⚙️ Configurando Sensores: **{d['name']}**")
                        try:
                            r_curr = requests.get(f"{API_URL}/devices/{d['id']}/sensors")
                            current_ids = r_curr.json() if r_curr.status_code == 200 else []
                        except: current_ids = []
                        default_names = [name for name, sid in sensor_options.items() if sid in current_ids]
                        
                        with st.form(f"config_sensors_{d['id']}"):
                            selected_names = st.multiselect("Sensores vinculados:", options=list(sensor_options.keys()), default=default_names)
                            c_save, c_canc = st.columns([1, 4])
                            if c_save.form_submit_button("💾 Salvar"):
                                new_ids = [sensor_options[name] for name in selected_names]
                                requests.post(f"{API_URL}/devices/{d['id']}/sensors", json={"sensor_ids": new_ids})
                                st.session_state["configuring_id"] = None
                                st.rerun()
                            if c_canc.form_submit_button("Cancelar"):
                                st.session_state["configuring_id"] = None
                                st.rerun()

                elif st.session_state["editing_id"] == d["id"]:
                     with st.container():
                        with st.form(f"edit_form_{d['id']}"):
                            ec1, ec2, ec3 = st.columns(3)
                            n_name = ec1.text_input("Nome", value=d["name"])
                            n_slug = ec2.text_input("Slug", value=d["slug"])
                            n_loc = ec3.text_input("Local", value=d["location"] or "")
                            if st.form_submit_button("💾 Salvar"):
                                requests.patch(f"{API_URL}/devices/{d['id']}", json={"name": n_name, "slug": n_slug, "location": n_loc})
                                st.session_state["editing_id"] = None
                                st.rerun()

                else:
                    # --- LINHA DE VISUALIZAÇÃO ---
                    c = st.columns([0.5, 2, 2, 1.5, 1, 2.5])
                    c[0].write(f"#{d['id']}")
                    c[1].write(f"**{d['name']}**")
                    c[2].code(d['slug'])
                    c[3].write(d['location'])
                    
                    status_icon = "🟢" if d['is_active'] else "🔴"
                    c[4].write(status_icon)
                    
                    b1, b2, b3 = c[5].columns(3)
                    
                    if b1.button("✏️", key=f"edit_{d['id']}"):
                        st.session_state["editing_id"] = d["id"]
                        st.session_state["configuring_id"] = None
                        st.rerun()
                    
                    if b2.button("⚙️", key=f"conf_{d['id']}"):
                        st.session_state["configuring_id"] = d["id"]
                        st.session_state["editing_id"] = None
                        st.rerun()

                    # --- AQUI ESTÁ A MÁGICA DO CALLBACK ---
                    icon_del = "⛔" if d['is_active'] else "♻️"
                    b3.button(
                        icon_del, 
                        key=f"toggle_{d['id']}",
                        help="Arquivar/Ativar",
                        # O 'on_click' roda a função ANTES do script recarregar
                        on_click=alternar_status_device,
                        args=(d['id'], d['is_active'])
                    )
                
                st.divider()

    except Exception as e:
        st.error(f"Erro ao carregar lista: {e}")