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