import streamlit as st
import requests
from app.dashboard.utils import API_URL

# FUNÇÃO CALLBACK
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
    
    # GERENCIAMENTO DE ESTADO
    if "editing_id" not in st.session_state: st.session_state["editing_id"] = None
    if "configuring_id" not in st.session_state: st.session_state["configuring_id"] = None
    if "feedback_msg" not in st.session_state: st.session_state["feedback_msg"] = None
    if "feedback_type" not in st.session_state: st.session_state["feedback_type"] = None

    # Exibe mensagens de feedback
    if st.session_state["feedback_msg"]:
        tipo = st.session_state["feedback_type"]
        msg = st.session_state["feedback_msg"]
        if tipo == "success": st.success(msg)
        elif tipo == "warning": st.warning(msg)
        else: st.error(msg)
        st.session_state["feedback_msg"] = None

    # CADASTRO
    with st.form("cadastro_device"):
        st.write("### Novo Dispositivo")
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome", placeholder="Ex: Arduino Lab 1")
        slug = c2.text_input("Slug (ID Único)", placeholder="Ex: arduino-lab-1")
        
        c3, c4 = st.columns(2)
        local = c3.text_input("Localização", placeholder="Ex: Bancada A")
        
        try:
            r_types = requests.get(f"{API_URL}/sensor-types/")
            opcoes_sensores = {s['name']: s['id'] for s in r_types.json()} if r_types.status_code == 200 else {}
        except:
            opcoes_sensores = {}
            
        selected_sensors = c4.multiselect("Vincular Sensores (Opcional)", options=list(opcoes_sensores.keys()))

        if st.form_submit_button("Cadastrar Dispositivo"):
            
            if not name or not slug:
                st.error("⚠️ Nome e Slug são obrigatórios!")
            else:
                ids_escolhidos = [opcoes_sensores[name] for name in selected_sensors]

                payload = {
                    "name": name, 
                    "slug": slug, 
                    "location": local or None, #
                    "is_active": True,
                    "sensor_ids": ids_escolhidos
                }
                
                try:
                    r = requests.post(f"{API_URL}/devices/", json=payload)
                    
                    if r.status_code == 200:
                        st.success(f"Dispositivo '{name}' criado com sucesso!")
                        st.rerun()
                    
                    elif r.status_code == 422:
                        erro_json = r.json()
                        detalhes = erro_json.get("detail", [])
                        msg_final = "Erro de Validação:\n"
                        
                        if isinstance(detalhes, list):
                            for err in detalhes:
                                campo = err.get("loc", ["?"])[-1]
                                msg = err.get("msg", "")
                                msg_final += f"- **{campo}**: {msg}\n"
                        else:
                            msg_final += str(detalhes)
                            
                        st.error(msg_final)
                        
                    else:
                        st.error(f"Erro ({r.status_code}): {r.text}")

                except Exception as e:
                    st.error(f"Erro Conexão: {e}")

    st.divider()
    
    # LISTAGEM
    try:
        res = requests.get(f"{API_URL}/devices/")
        devices = res.json() if res.status_code == 200 else []
        
        # Carrega tipos para o formulário de vínculo
        res_types = requests.get(f"{API_URL}/sensor-types/")
        sensor_types = res_types.json() if res_types.status_code == 200 else []
        # Mapa Nome -> ID
        sensor_options = {s['name']: s['id'] for s in sensor_types}
        # Mapa ID -> Nome (para reconstruir nomes no multiselect se necessário)
        sensor_id_map = {s['id']: s['name'] for s in sensor_types}
        
        if not devices:
            st.info("Nenhum dispositivo cadastrado.")
        else:
            mostrar_arquivados = st.checkbox("Mostrar Dispositivos Arquivados", value=True)
            devices_filtrados = [d for d in devices if d['is_active'] or mostrar_arquivados]

            cols = st.columns([0.5, 2, 2, 1.5, 1, 2.5])
            cols[0].markdown("**ID**")
            cols[1].markdown("**Nome & Sensores**") # Título ajustado
            cols[2].markdown("**Slug**")
            cols[3].markdown("**Local**")
            cols[4].markdown("**Status**")
            cols[5].markdown("**Ações**")
            st.markdown("---")

            for d in devices_filtrados:
                
                # MODO CONFIGURAÇÃO (VÍNCULOS)
                if st.session_state["configuring_id"] == d["id"]:
                    with st.container(border=True):
                        st.info(f"⚙️ Configurando Sensores: **{d['name']}**")
                        
                        # Agora podemos pegar os sensores direto do objeto device (Performance++)
                        # Mas para garantir integridade caso a lista esteja defasada, mantemos a chamada GET específica ou usamos a lista local
                        current_sensors_objs = d.get('sensors', [])
                        current_ids = [s['id'] for s in current_sensors_objs]
                        
                        # Filtra nomes baseados nos IDs atuais
                        default_names = [sensor_id_map[sid] for sid in current_ids if sid in sensor_id_map]
                        
                        with st.form(f"config_sensors_{d['id']}"):
                            selected_names = st.multiselect(
                                "Quais sensores este dispositivo possui?",
                                options=list(sensor_options.keys()),
                                default=default_names
                            )
                            
                            c_save, c_canc = st.columns([1, 4])
                            if c_save.form_submit_button("💾 Salvar Vínculo"):
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

                # MODO EDIÇÃO (CAMPOS BÁSICOS)
                elif st.session_state["editing_id"] == d["id"]:
                    with st.container():
                        st.info(f"Editando: {d['name']}")
                        with st.form(f"edit_form_{d['id']}"):
                            ec1, ec2, ec3 = st.columns(3)
                            n_name = ec1.text_input("Nome", value=d["name"])
                            n_slug = ec2.text_input("Slug", value=d["slug"])
                            n_loc = ec3.text_input("Local", value=d["location"] or "")
                            
                            if st.form_submit_button("💾 Salvar"):
                                try:
                                    requests.patch(f"{API_URL}/devices/{d['id']}", json={"name": n_name, "slug": n_slug, "location": n_loc})
                                    st.session_state["editing_id"] = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {e}")

                # MODO VISUALIZAÇÃO 
                else:
                    c = st.columns([0.5, 2, 2, 1.5, 1, 2.5])
                    c[0].write(f"#{d['id']}")
                    
                    with c[1]:
                        st.write(f"**{d['name']}**")
                        sensores = d.get('sensors', [])
                        if sensores:
                            tags_html = ""
                            for s in sensores:
                                is_sensor_active = s.get('is_active', True)
                                
                                bg_color = "#297A17" if is_sensor_active else "#555"
                                opacity = "1.0" if is_sensor_active else "0.6"
                                tooltip = "Ativo" if is_sensor_active else "Arquivado (Desativado)"
                                
                                style = f"""
                                    background-color:{bg_color}; 
                                    color:white; 
                                    padding:2px 8px; 
                                    border-radius:12px; 
                                    font-size:0.75em; 
                                    margin-right:4px; 
                                    opacity:{opacity};
                                    display:inline-block;
                                    margin-bottom:2px;
                                """
                                tags_html += f"<span style='{style}' title='{tooltip}'>{s['name']}</span>"
                            
                            st.markdown(tags_html, unsafe_allow_html=True)
                        else:
                            st.caption("Sem sensores")

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

                    icon_del = "⛔" if d['is_active'] else "♻️"
                    b3.button(
                        icon_del, 
                        key=f"toggle_{d['id']}",
                        help="Arquivar/Ativar",
                        on_click=alternar_status_device,
                        args=(d['id'], d['is_active'])
                    )
                
                st.divider()

    except Exception as e:
        st.error(f"Erro ao carregar lista: {e}")