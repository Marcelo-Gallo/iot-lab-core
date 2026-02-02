import streamlit as st
import requests
from app.dashboard.utils import API_URL, get_device_tokens, create_device_token

# --- HELPER DE AUTENTICAÇÃO ---
def get_auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

# --- HELPER DE STATUS (PATCH) ---
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

# --- RENDERIZAÇÃO DA VIEW ---
def render_devices_view():
    st.title("📡 Gerenciamento de Dispositivos")
    
    headers = get_auth_headers()
    
    # INICIALIZAÇÃO DE ESTADO
    if "editing_id" not in st.session_state: st.session_state["editing_id"] = None
    if "configuring_id" not in st.session_state: st.session_state["configuring_id"] = None
    if "feedback_msg" not in st.session_state: st.session_state["feedback_msg"] = None
    if "feedback_type" not in st.session_state: st.session_state["feedback_type"] = None

    # EXIBIÇÃO DE FEEDBACK
    if st.session_state["feedback_msg"]:
        tipo = st.session_state["feedback_type"]
        msg = st.session_state["feedback_msg"]
        if tipo == "success": st.success(msg)
        elif tipo == "warning": st.warning(msg)
        else: st.error(msg)
        st.session_state["feedback_msg"] = None

    # --- 1. FORMULÁRIO DE CADASTRO ---
    with st.expander("➕ Novo Dispositivo", expanded=False):
        with st.form("cadastro_device"):
            st.write("### Novo Dispositivo")
            c1, c2 = st.columns(2)
            name = c1.text_input("Nome", placeholder="Ex: Arduino Lab 1")
            slug = c2.text_input("Slug (ID Único)", placeholder="Ex: arduino-lab-1")
            
            c3, c4 = st.columns(2)
            local = c3.text_input("Localização", placeholder="Ex: Bancada A")
            
            # [NOVO] Checkbox de Bateria
            is_battery = c4.checkbox("🔋 Bateria / Deep Sleep", help="Marque se o dispositivo usa bateria e dorme.")
            
            # Busca Sensores
            try:
                r_types = requests.get(f"{API_URL}/sensor-types/", headers=headers)
                opcoes_sensores = {s['name']: s['id'] for s in r_types.json()} if r_types.status_code == 200 else {}
            except:
                opcoes_sensores = {}
                
            selected_sensors = st.multiselect("Vincular Sensores (Opcional)", options=list(opcoes_sensores.keys()))

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
                        "is_battery_powered": is_battery, # [NOVO]
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

    # --- 2. LISTAGEM DE DISPOSITIVOS ---
    try:
        res = requests.get(f"{API_URL}/devices/", headers=headers)
        if res.status_code == 401:
            st.warning("🔒 Faça login para ver os dispositivos.")
            return

        devices = res.json() if res.status_code == 200 else []
        
        # Mapeamento para o SelectBox da Área de Segurança
        device_map_options = {f"{d['id']} - {d['name']}": d['id'] for d in devices if d['is_active']}

        # Mapeamento de Sensores
        res_types = requests.get(f"{API_URL}/sensor-types/", headers=headers)
        sensor_types = res_types.json() if res_types.status_code == 200 else []
        sensor_options = {s['name']: s['id'] for s in sensor_types}
        sensor_id_map = {s['id']: s['name'] for s in sensor_types}
        
        if not devices:
            st.info("Nenhum dispositivo cadastrado.")
        else:
            mostrar_arquivados = st.checkbox("Mostrar Dispositivos Arquivados", value=True)
            devices_filtrados = [d for d in devices if d['is_active'] or mostrar_arquivados]

            # Cabeçalho da Tabela
            cols = st.columns([0.5, 2.5, 2, 1.5, 1, 2.5])
            cols[0].markdown("**ID**")
            cols[1].markdown("**Nome**") 
            cols[2].markdown("**Slug**")
            cols[3].markdown("**Local**")
            cols[4].markdown("**Status**")
            cols[5].markdown("**Ações**")
            st.markdown("---")

            for d in devices_filtrados:
                
                # --- MODO DE CONFIGURAÇÃO (SENSORES & CALIBRAÇÃO) ---
                if st.session_state["configuring_id"] == d["id"]:
                    with st.container(border=True):
                        st.info(f"⚙️ Configurando: **{d['name']}**")
                        
                        current_sensors_objs = d.get('sensors', [])
                        current_ids = [s['id'] for s in current_sensors_objs]
                        default_names = [sensor_id_map[sid] for sid in current_ids if sid in sensor_id_map]
                        
                        # A. Vínculo de Sensores
                        with st.form(f"config_sensors_{d['id']}"):
                            st.write("**1. Sensores Vinculados**")
                            selected_names = st.multiselect("Selecionar:", options=list(sensor_options.keys()), default=default_names)
                            
                            if st.form_submit_button("💾 Salvar Lista de Sensores"):
                                new_ids = [sensor_options[name] for name in selected_names]
                                try:
                                    requests.post(f"{API_URL}/devices/{d['id']}/sensors", json={"sensor_ids": new_ids}, headers=headers)
                                    st.toast("Lista de sensores atualizada!")
                                    st.rerun()
                                except: pass
                        
                        # B. [NOVO] Calibração Individual
                        if current_sensors_objs:
                            st.write("**2. Calibração (Fórmulas Matemáticas)**")
                            st.caption("Use 'x' como valor bruto. Ex: `x * 0.5 + 10`")
                            
                            for s in current_sensors_objs:
                                c_name, c_form, c_btn = st.columns([1, 2, 1])
                                c_name.write(f"🧬 {s['name']}")
                                
                                # Busca fórmula atual (Fetch On-Demand para garantir dado fresco)
                                form_key = f"form_val_{d['id']}_{s['id']}"
                                try:
                                    r_calib = requests.get(f"{API_URL}/devices/{d['id']}/sensors/{s['id']}/calibration", headers=headers)
                                    current_formula = r_calib.json().get("formula") or ""
                                except: current_formula = ""

                                new_formula = c_form.text_input(
                                    "Fórmula", 
                                    value=current_formula, 
                                    key=f"input_form_{d['id']}_{s['id']}", 
                                    label_visibility="collapsed",
                                    placeholder="Ex: x / 2"
                                )
                                
                                if c_btn.button("Salvar", key=f"btn_save_{d['id']}_{s['id']}"):
                                    try:
                                        requests.put(
                                            f"{API_URL}/devices/{d['id']}/sensors/{s['id']}/calibration",
                                            json={"calibration_formula": new_formula},
                                            headers=headers
                                        )
                                        st.toast(f"Calibração de {s['name']} salva!")
                                    except Exception as e:
                                        st.error(f"Erro: {e}")

                        if st.button("Fechar Configuração", key=f"close_{d['id']}"):
                            st.session_state["configuring_id"] = None
                            st.rerun()
                
                # --- MODO DE EDIÇÃO (DADOS BÁSICOS) ---
                elif st.session_state["editing_id"] == d["id"]:
                    with st.container():
                        with st.form(f"edit_form_{d['id']}"):
                            st.write(f"📝 Editando **{d['name']}**")
                            ec1, ec2, ec3 = st.columns(3)
                            n_name = ec1.text_input("Nome", value=d["name"])
                            n_slug = ec2.text_input("Slug", value=d["slug"])
                            n_loc = ec3.text_input("Local", value=d["location"] or "")
                            
                            # [NOVO] Edição de Bateria
                            n_batt = st.checkbox("🔋 Alimentado por Bateria", value=d.get('is_battery_powered', False))

                            if st.form_submit_button("💾 Atualizar Dados"):
                                try:
                                    requests.patch(
                                        f"{API_URL}/devices/{d['id']}", 
                                        json={
                                            "name": n_name, 
                                            "slug": n_slug, 
                                            "location": n_loc,
                                            "is_battery_powered": n_batt # [NOVO]
                                        }, 
                                        headers=headers
                                    )
                                    st.session_state["editing_id"] = None
                                    st.rerun()
                                except: pass

                # --- MODO DE VISUALIZAÇÃO (PADRÃO) ---
                else:
                    c = st.columns([0.5, 2.5, 2, 1.5, 1, 2.5])
                    c[0].write(f"#{d['id']}")
                    
                    with c[1]:
                        # [NOVO] Ícone de Bateria no nome
                        batt_icon = "🔋 " if d.get('is_battery_powered') else "⚡ "
                        st.write(f"**{batt_icon}{d['name']}**")
                        
                        # Tags de sensores
                        sensores = d.get('sensors', [])
                        if sensores:
                            tags_html = ""
                            for s in sensores:
                                is_active = s.get('is_active', True)
                                color = "#297A17" if is_active else "#555"
                                tags_html += f"<span style='background-color:{color}; color:white; padding:2px 6px; border-radius:4px; font-size:0.75em; margin-right:4px;'>{s['name']}</span>"
                            st.markdown(tags_html, unsafe_allow_html=True)
                        else: st.caption("Sem sensores")
                        
                    c[2].code(d['slug'])
                    c[3].write(d['location'])
                    c[4].write("🟢" if d['is_active'] else "🔴")
                    
                    b1, b2, b3 = c[5].columns(3)
                    if b1.button("✏️", key=f"ed_{d['id']}", help="Editar Nome/Local/Bateria"): 
                        st.session_state["editing_id"] = d["id"]
                        st.session_state["configuring_id"] = None
                        st.rerun()
                    if b2.button("⚙️", key=f"cf_{d['id']}", help="Configurar Sensores e Calibração"): 
                        st.session_state["configuring_id"] = d["id"]
                        st.session_state["editing_id"] = None
                        st.rerun()
                    
                    # Botão de Arquivar/Ativar
                    icon_btn = "⛔" if d['is_active'] else "♻️"
                    b3.button(icon_btn, key=f"tg_{d['id']}", on_click=alternar_status_device, args=(d['id'], d['is_active']))
                
                st.divider()

        # --- 3. ÁREA DE SEGURANÇA (TOKEN MANAGEMENT) ---
        st.subheader("🔐 Área de Segurança")
        with st.expander("Gerenciar API Keys (Tokens de Hardware)"):
            st.info("Gere tokens para autenticar seus dispositivos físicos (ESP32/Arduino) sem expor senhas de usuário.")
            
            if not device_map_options:
                st.warning("Nenhum dispositivo ativo disponível para gerar tokens.")
            else:
                selected_label = st.selectbox("Selecione o Dispositivo:", list(device_map_options.keys()))
                selected_dev_id = device_map_options[selected_label]
                
                st.markdown(f"**Chaves Ativas de: {selected_label}**")
                # Assume que get_device_tokens retorna lista de dicts com 'label', 'created_at'
                tokens = get_device_tokens(selected_dev_id)
                
                if tokens:
                    for t in tokens:
                        col_t1, col_t2 = st.columns([3, 1])
                        # Ajuste conforme seu retorno real do utils.py
                        label = t.get('label', 'Sem Rótulo') 
                        created = t.get('created_at', '')[:10]
                        col_t1.text(f"🔑 {label} (Criado em: {created})")
                        # Futuro: Botão de revogar
                else:
                    st.caption("🚫 Nenhuma chave gerada.")

                st.divider()
                
                st.write("#### 🆕 Gerar Nova Chave")
                with st.form(key=f"form_token_gen"):
                    new_token_label = st.text_input("Rótulo da Chave", placeholder="Ex: ESP32 Produção", value="Token Padrão")
                    if st.form_submit_button("Gerar Token Seguro"):
                        token_data = create_device_token(selected_dev_id, new_token_label)
                        if token_data:
                            st.success("✅ Token gerado!")
                            st.warning("⚠️ COPIE AGORA! Por segurança, ele não será exibido novamente.")
                            st.code(token_data.get("token"), language="text")

    except Exception as e:
        st.error(f"Erro ao carregar lista: {e}")