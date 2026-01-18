import streamlit as st
import requests
from app.dashboard.utils import API_URL

def render_devices_view():
    st.title("📡 Gerenciamento de Dispositivos")
    
    # --- 1. GERENCIAMENTO DE ESTADO LOCAL ---
    if "editing_id" not in st.session_state: st.session_state["editing_id"] = None
    if "feedback_msg" not in st.session_state: st.session_state["feedback_msg"] = None
    if "feedback_type" not in st.session_state: st.session_state["feedback_type"] = None

    if st.session_state["feedback_msg"]:
        if st.session_state["feedback_type"] == "success": st.success(st.session_state["feedback_msg"])
        elif st.session_state["feedback_type"] == "warning": st.warning(st.session_state["feedback_msg"])
        else: st.error(st.session_state["feedback_msg"])
        st.session_state["feedback_msg"] = None

    # --- 2. CADASTRO ---
    with st.form("cadastro_device"):
        st.write("### Novo Dispositivo")
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome", placeholder="Ex: Arduino Lab 1")
        slug = c2.text_input("Slug (ID Único)", placeholder="Ex: arduino-lab-1")
        c3, c4 = st.columns(2)
        local = c3.text_input("Localização", placeholder="Ex: Bancada A")
        # Sem checkbox (Padrão Ativo)
        
        if st.form_submit_button("Cadastrar Dispositivo"):
            payload = {"name": name, "slug": slug, "location": local, "is_active": True}
            try:
                r = requests.post(f"{API_URL}/devices/", json=payload)
                if r.status_code == 200:
                    st.session_state["feedback_msg"] = f"Dispositivo '{name}' criado!"
                    st.session_state["feedback_type"] = "success"
                    st.rerun()
                else:
                    st.session_state["feedback_msg"] = f"Erro: {r.json().get('detail', 'Desconhecido')}"
                    st.session_state["feedback_type"] = "error"
                    st.rerun()
            except Exception as e:
                st.error(f"Erro Conexão: {e}")

    st.divider()
    
    # --- 3. LISTAGEM ---
    try:
        res = requests.get(f"{API_URL}/devices/")
        devices = res.json() if res.status_code == 200 else []
        
        if not devices:
            st.info("Nenhum dispositivo cadastrado.")
        else:
            # Opção de Filtro (Para limpar a visualização se quiser)
            mostrar_arquivados = st.checkbox("Mostrar Dispositivos Arquivados (Inativos)", value=True)
            
            # Filtra a lista localmente baseada na escolha
            devices_filtrados = [d for d in devices if d['is_active'] or mostrar_arquivados]

            cols = st.columns([0.5, 2, 2, 2, 1, 1.5])
            cols[0].markdown("**ID**")
            cols[1].markdown("**Nome**")
            cols[2].markdown("**Slug**")
            cols[3].markdown("**Local**")
            cols[4].markdown("**Status**")
            cols[5].markdown("**Ações**")
            st.markdown("---")

            for d in devices_filtrados:
                # --- MODO EDIÇÃO ---
                if st.session_state["editing_id"] == d["id"]:
                    with st.container():
                        st.info(f"Editando: {d['name']}")
                        with st.form(f"edit_form_{d['id']}"):
                            ec1, ec2, ec3 = st.columns(3)
                            n_name = ec1.text_input("Nome", value=d["name"])
                            n_slug = ec2.text_input("Slug", value=d["slug"])
                            n_loc = ec3.text_input("Local", value=d["location"] or "")
                            
                            if st.form_submit_button("💾 Salvar"):
                                try:
                                    patch_data = {"name": n_name, "slug": n_slug, "location": n_loc}
                                    r_up = requests.patch(f"{API_URL}/devices/{d['id']}", json=patch_data)
                                    if r_up.status_code == 200:
                                        st.session_state["feedback_msg"] = "Atualizado!"
                                        st.session_state["feedback_type"] = "success"
                                        st.session_state["editing_id"] = None
                                        st.rerun()
                                    else:
                                        st.error(f"Erro: {r_up.text}")
                                except Exception as e:
                                    st.error(f"Erro: {e}")

                # --- MODO VISUALIZAÇÃO ---
                else:
                    c = st.columns([0.5, 2, 2, 2, 1, 1.5])
                    c[0].write(f"#{d['id']}")
                    c[1].write(f"**{d['name']}**")
                    c[2].code(d['slug'])
                    c[3].write(d['location'])
                    
                    status_icon = "🟢" if d['is_active'] else "🔴"
                    c[4].write(status_icon)
                    
                    b1, b2 = c[5].columns(2)
                    
                    if b1.button("✏️", key=f"edit_{d['id']}"):
                        st.session_state["editing_id"] = d["id"]
                        st.rerun()
                    
                    # LÓGICA SEGURA: TOGGLE (Ativar/Desativar)
                    # Nunca deleta, apenas alterna o estado.
                    if d['is_active']:
                        btn_label = "⛔"
                        btn_help = "Arquivar (Desativar)"
                        novo_status = False
                        msg_sucesso = "Dispositivo arquivado."
                    else:
                        btn_label = "♻️"
                        btn_help = "Restaurar (Reativar)"
                        novo_status = True
                        msg_sucesso = "Dispositivo reativado."

                    if b2.button(btn_label, key=f"toggle_{d['id']}", help=btn_help):
                        try:
                            # Usa PATCH para mudar apenas o status
                            r = requests.patch(f"{API_URL}/devices/{d['id']}", json={"is_active": novo_status})
                            if r.status_code == 200:
                                st.session_state["feedback_msg"] = msg_sucesso
                                st.session_state["feedback_type"] = "warning" if not novo_status else "success"
                                st.rerun()
                            else:
                                st.error(f"Erro: {r.text}")
                        except Exception as e:
                            st.error(f"Erro: {e}")
                
                st.divider()

    except Exception as e:
        st.error(f"Erro ao carregar dispositivos: {e}")