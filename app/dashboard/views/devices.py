import streamlit as st
import requests
from app.dashboard.utils import API_URL, get_device_tokens, create_device_token

def get_auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def alternar_status_device(device_id, status_atual):
    novo_status = not status_atual
    headers = get_auth_headers()
    
    try:
        r = requests.patch(
            f"{API_URL}/devices/{device_id}", 
            json={"is_active": novo_status},
            headers=headers 
        )
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
    
    headers = get_auth_headers()
    
    # GERENCIAMENTO DE ESTADO
    if "editing_id" not in st.session_state: st.session_state["editing_id"] = None
    if "configuring_id" not in st.session_state: st.session_state["configuring_id"] = None
    if "feedback_msg" not in st.session_state: st.session_state["feedback_msg"] = None
    if "feedback_type" not in st.session_state: st.session_state["feedback_type"] = None

    # FEEDBACK VISUAL
    if st.session_state["feedback_msg"]:
        tipo = st.session_state["feedback_type"]
        msg = st.session_state["feedback_msg"]
        if tipo == "success": st.success(msg)
        elif tipo == "warning": st.warning(msg)
        else: st.error(msg)
        st.session_state["feedback_msg"] = None

    with st.form("cadastro_device"):
        st.write("### Novo Dispositivo")
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome", placeholder="Ex: Arduino Lab 1")
        slug = c2.text_input("Slug (ID Único)", placeholder="Ex: arduino-lab-1")
        
        c3, c4 = st.columns(2)
        local = c3.text_input("Localização", placeholder="Ex: Bancada A")
        
        # Busca tipos de sensores
        try:
            r_types = requests.get(f"{API_URL}/sensor-types/", headers=headers)
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
                    "location": local or None, 
                    "is_active": True,
                    "sensor_ids": ids_escolhidos
                }
                try:
                    r = requests.post(f"{API_URL}/devices/", json=payload, headers=headers)
                    if r.status_code == 200:
                        st.success(f"Dispositivo '{name}' criado com sucesso!")
                        st.rerun()
                    elif r.status_code == 422:
                        st.error(f"Erro de Validação: {r.json().get('detail')}")
                    elif r.status_code == 401:
                        st.error("⛔ Sessão expirada.")
                    else:
                        st.error(f"Erro ({r.status_code}): {r.text}")
                except Exception as e:
                    st.error(f"Erro Conexão: {e}")

    st.divider()

    try:
        res = requests.get(f"{API_URL}/devices/", headers=headers)
        if res.status_code == 401:
            st.warning("🔒 Faça login para ver os dispositivos.")
            return

        devices = res.json() if res.status_code == 200 else []
        
        device_map_options = {f"{d['id']} - {d['name']}": d['id'] for d in devices if d['is_active']}

        res_types = requests.get(f"{API_URL}/sensor-types/", headers=headers)
        sensor_types = res_types.json() if res_types.status_code == 200 else []
        sensor_options = {s['name']: s['id'] for s in sensor_types}
        sensor_id_map = {s['id']: s['name'] for s in sensor_types}
        
        if not devices:
            st.info("Nenhum dispositivo cadastrado.")
        else:
            mostrar_arquivados = st.checkbox("Mostrar Dispositivos Arquivados", value=True)
            devices_filtrados = [d for d in devices if d['is_active'] or mostrar_arquivados]

            cols = st.columns([0.5, 2, 2, 1.5, 1, 2.5])
            cols[0].markdown("**ID**")
            cols[1].markdown("**Nome & Sensores**") 
            cols[2].markdown("**Slug**")
            cols[3].markdown("**Local**")
            cols[4].markdown("**Status**")
            cols[5].markdown("**Ações**")
            st.markdown("---")

            for d in devices_filtrados:
                
                if st.session_state["configuring_id"] == d["id"]:
                    with st.container(border=True):
                        st.info(f"⚙️ Configurando Sensores: **{d['name']}**")
                        current_sensors_objs = d.get('sensors', [])
                        current_ids = [s['id'] for s in current_sensors_objs]
                        default_names = [sensor_id_map[sid] for sid in current_ids if sid in sensor_id_map]
                        
                        with st.form(f"config_sensors_{d['id']}"):
                            selected_names = st.multiselect("Sensores:", options=list(sensor_options.keys()), default=default_names)
                            if st.form_submit_button("💾 Salvar Vínculo"):
                                new_ids = [sensor_options[name] for name in selected_names]
                                try:
                                    requests.post(f"{API_URL}/devices/{d['id']}/sensors", json={"sensor_ids": new_ids}, headers=headers)
                                    st.session_state["configuring_id"] = None
                                    st.rerun()
                                except: pass
                
                elif st.session_state["editing_id"] == d["id"]:
                    with st.container():
                        with st.form(f"edit_form_{d['id']}"):
                            ec1, ec2, ec3 = st.columns(3)
                            n_name = ec1.text_input("Nome", value=d["name"])
                            n_slug = ec2.text_input("Slug", value=d["slug"])
                            n_loc = ec3.text_input("Local", value=d["location"] or "")
                            if st.form_submit_button("💾 Salvar"):
                                try:
                                    requests.patch(f"{API_URL}/devices/{d['id']}", json={"name": n_name, "slug": n_slug, "location": n_loc}, headers=headers)
                                    st.session_state["editing_id"] = None
                                    st.rerun()
                                except: pass

                else:
                    c = st.columns([0.5, 2, 2, 1.5, 1, 2.5])
                    c[0].write(f"#{d['id']}")
                    with c[1]:
                        st.write(f"**{d['name']}**")
                        sensores = d.get('sensors', [])
                        if sensores:
                            tags_html = ""
                            for s in sensores:
                                is_active = s.get('is_active', True)
                                color = "#297A17" if is_active else "#555"
                                tags_html += f"<span style='background-color:{color}; color:white; padding:2px 6px; border-radius:4px; font-size:0.8em; margin-right:4px;'>{s['name']}</span>"
                            st.markdown(tags_html, unsafe_allow_html=True)
                        else: st.caption("Sem sensores")
                    c[2].code(d['slug'])
                    c[3].write(d['location'])
                    c[4].write("🟢" if d['is_active'] else "🔴")
                    
                    b1, b2, b3 = c[5].columns(3)
                    if b1.button("✏️", key=f"ed_{d['id']}"): 
                        st.session_state["editing_id"] = d["id"]
                        st.rerun()
                    if b2.button("⚙️", key=f"cf_{d['id']}"): 
                        st.session_state["configuring_id"] = d["id"]
                        st.rerun()
                    b3.button("⛔" if d['is_active'] else "♻️", key=f"tg_{d['id']}", on_click=alternar_status_device, args=(d['id'], d['is_active']))
                
                st.divider()

        st.subheader("🔐 Área de Segurança")
        with st.expander("Gerenciar API Keys (Tokens de Hardware)"):
            st.info("Gere tokens para autenticar seus dispositivos físicos (ESP32/Arduino) sem expor senhas de usuário.")
            
            if not device_map_options:
                st.warning("Nenhum dispositivo ativo disponível para gerar tokens.")
            else:
                selected_label = st.selectbox("Selecione o Dispositivo:", list(device_map_options.keys()))
                selected_dev_id = device_map_options[selected_label]
                
                st.markdown(f"**Chaves Ativas de: {selected_label}**")
                tokens = get_device_tokens(selected_dev_id)
                
                if tokens:
                    for t in tokens:
                        col_t1, col_t2 = st.columns([3, 1])
                        col_t1.text(f"🔑 {t['label']} (Criado em: {t['created_at'][:10]})")
                else:
                    st.caption("🚫 Nenhuma chave gerada.")

                st.divider()
                
                # 3. Gerar Novo Token
                st.write("#### 🆕 Gerar Nova Chave")
                with st.form(key=f"form_token_gen"):
                    new_token_label = st.text_input("Rótulo da Chave", placeholder="Ex: ESP32 Produção", value="Token Padrão")
                    if st.form_submit_button("Gerar Token Seguro"):
                        token_data = create_device_token(selected_dev_id, new_token_label)
                        if token_data:
                            st.success("✅ Token gerado!")
                            st.warning("⚠️ COPIE AGORA! Por segurança, ele não será exibido novamente.")
                            st.code(token_data["token"], language="text")
                            # st.rerun() # Opcional: força reload, mas esconde o token recém gerado. Melhor deixar sem.

    except Exception as e:
        st.error(f"Erro ao carregar lista: {e}")