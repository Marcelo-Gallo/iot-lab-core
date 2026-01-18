import streamlit as st

# --- 1. CONFIGURAÇÃO WIDE ---
st.set_page_config(page_title="Gerenciamento", layout="wide", page_icon="⚙️")

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.api_service import get_all_devices, create_device, patch_device

st.title("⚙️ Gerenciamento de Dispositivos")

if "edit_id" not in st.session_state: st.session_state.edit_id = None

# Cadastro
with st.form("new_dev"):
    st.write("### Novo Dispositivo")
    c1, c2 = st.columns(2)
    name = c1.text_input("Nome")
    slug = c2.text_input("Slug")
    loc = st.text_input("Local")
    if st.form_submit_button("Criar"):
        res = create_device({"name": name, "slug": slug, "location": loc, "is_active": True})
        if res.status_code == 200: st.success("Criado!")
        else: st.error(res.text)

st.divider()

# Listagem
devices = get_all_devices()
if devices:
    cols = st.columns([0.5, 2, 2, 2, 1, 1.5])
    cols[0].write("**ID**"); cols[1].write("**Nome**"); cols[2].write("**Slug**")
    cols[3].write("**Local**"); cols[4].write("**Status**"); cols[5].write("**Ações**")
    st.write("---")

    for d in devices:
        is_active = d.get('is_active', True)
        if d.get('deleted_at'): is_active = False
        
        c = st.columns([0.5, 2, 2, 2, 1, 1.5])
        c[0].write(d['id'])
        
        if st.session_state.edit_id == d['id']:
            with st.form(f"edt_{d['id']}"):
                col_e = st.columns(3)
                nn = col_e[0].text_input("N", d['name'])
                ns = col_e[1].text_input("S", d['slug'])
                nl = col_e[2].text_input("L", d['location'])
                if st.form_submit_button("Salvar"):
                    patch_device(d['id'], {"name": nn, "slug": ns, "location": nl})
                    st.session_state.edit_id = None
                    st.rerun()
        else:
            c[1].write(d['name'])
            c[2].code(d['slug'])
            c[3].write(d['location'])
            c[4].write("🟢" if is_active else "🔴")
            
            b1, b2 = c[5].columns(2)
            if b1.button("✏️", key=f"e{d['id']}"): 
                st.session_state.edit_id = d['id']
                st.rerun()
            
            btn_txt = "🗑️" if is_active else "🔄"
            new_status = False if is_active else True
            help_txt = "Arquivar" if is_active else "Restaurar"
            
            if b2.button(btn_txt, key=f"d{d['id']}", help=help_txt):
                patch_device(d['id'], {"is_active": new_status, "deleted_at": None if new_status else None})
                st.rerun()
        st.divider()
else:
    st.info("Nenhum dispositivo encontrado.")