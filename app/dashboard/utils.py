import streamlit as st
import requests
import pytz
from datetime import datetime

# --- CONSTANTES ---
# No Docker, o backend é acessível por 'http://backend:8000'
API_URL = "http://backend:8000/api/v1"
WS_URL = "ws://backend:8000/api/v1/measurements/ws"
FUSO_BR = pytz.timezone("America/Sao_Paulo")

# --- FUNÇÕES ÚTEIS ---
def converter_para_local(iso_str):
    """Converte string UTC do banco para datetime Local (SP)"""
    if not iso_str: return None
    dt_utc = datetime.fromisoformat(iso_str).replace(tzinfo=pytz.UTC)
    return dt_utc.astimezone(FUSO_BR)

def carregar_mapa_sensores():
    """
    Retorna dicionário rico: {id: {'name': 'Temperatura', 'unit': '°C'}}
    Busca direto do banco.
    """
    try:
        response = requests.get(f"{API_URL}/sensor-types/")
        if response.status_code == 200:
            tipos = response.json()
            return {
                t['id']: {'name': t['name'], 'unit': t['unit']} 
                for t in tipos
            }
    except:
        pass
    # Fallback
    return {1: {'name': "Temperatura", 'unit': "°C"}, 2: {'name': "Umidade", 'unit': "%"}}

def get_device_tokens(device_id: int):
    """Busca os tokens de um dispositivo específico"""
    if not st.session_state.get("token"):
        return []
        
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        response = requests.get(
            f"{API_URL}/devices/{device_id}/tokens",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return []

def create_device_token(device_id: int, label: str):
    """Gera um novo token para o dispositivo"""
    if not st.session_state.get("token"):
        return None
        
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    payload = {"label": label}
    
    try:
        response = requests.post(
            f"{API_URL}/devices/{device_id}/tokens",
            json=payload,
            headers=headers
        )
        if response.status_code == 200:
            return response.json() # Retorna o token completo (com o segredo)
        else:
            st.error(f"Erro ao criar token: {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None