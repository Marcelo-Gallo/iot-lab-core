import requests
import streamlit as st

API_URL = "http://backend:8000/api/v1"

# --- CACHE (Como se fosse um Singleton de Serviço) ---
# Usamos @st.cache_data para não bater na API toda hora
def carregar_mapa_sensores():
    try:
        res = requests.get(f"{API_URL}/sensor-types/")
        if res.status_code == 200:
            return {t['id']: {'name': t['name'], 'unit': t['unit']} for t in res.json()}
    except: pass
    return {1: {'name': "Temperatura", 'unit': "°C"}, 2: {'name': "Umidade", 'unit': "%"}}

def get_active_devices_map():
    """Retorna mapa de devices e lista de IDs ativos"""
    d_map = {}
    active_ids = []
    try:
        res = requests.get(f"{API_URL}/devices/")
        if res.status_code == 200:
            for d in res.json():
                is_active = d.get('is_active', True)
                
                # ESTA LINHA É CRUCIAL PARA O FILTRO
                if d.get('deleted_at'): is_active = False 
                
                d_map[d['id']] = {
                    'name': d['name'], 
                    'active': is_active, # Guarda o status real aqui
                    'slug': d['slug'], 
                    'location': d['location']
                }
                
                if is_active:
                    active_ids.append(d['id'])
    except: pass
    return d_map, active_ids

def get_all_devices():
    try:
        res = requests.get(f"{API_URL}/devices/")
        return res.json() if res.status_code == 200 else []
    except: return []

# --- AÇÕES CRUD ---
def create_device(payload):
    return requests.post(f"{API_URL}/devices/", json=payload)

def patch_device(device_id, payload):
    return requests.patch(f"{API_URL}/devices/{device_id}", json=payload)

def fetch_historical_data(params):
    return requests.get(f"{API_URL}/measurements/", params=params)