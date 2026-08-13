import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime, timedelta

# Para rodar localmente, instale as dependências e execute:
# pip install streamlit pandas requests
# streamlit run dashboard.py

# ==========================================
# Configurações da Página e Variáveis Globais
# ==========================================
st.set_page_config(page_title="Irrigador Automático", page_icon="🌱", layout="wide")

API_URL = "http://localhost:8000"

# Use False para consumir da API real em vez de dados mockados
USE_MOCK_DATA = False

# ==========================================
# Funções de Comunicação com a API / Mocks
# ==========================================
def get_devices():
    if USE_MOCK_DATA:
        return [
            {"id": 1, "name": "ESP32 Horta", "mqtt_client_id": "esp32-vaso-01"},
            {"id": 2, "name": "ESP32 Estufa", "mqtt_client_id": "esp32-estufa-02"}
        ]
    try:
        req = requests.get(f"{API_URL}/devices/")
        if req.status_code == 200:
            return req.json()
    except Exception as e:
        st.sidebar.error(f"Erro ao conectar com API de Devices: {e}")
    return []

def get_plants():
    """Busca as plantas para fazer a relação device_id -> plant_id"""
    if USE_MOCK_DATA:
        return [
            {"id": 10, "device_id": 1, "name": "Tomates", "min_moisture": 40.0, "max_moisture": 80.0},
            {"id": 20, "device_id": 2, "name": "Orquídeas", "min_moisture": 50.0, "max_moisture": 70.0}
        ]
    try:
        req = requests.get(f"{API_URL}/plants/")
        if req.status_code == 200:
            return req.json()
    except Exception as e:
        st.sidebar.error(f"Erro ao conectar com API de Plants: {e}")
    return []

def get_history(plant_id, limit=60):
    if USE_MOCK_DATA:
        now = datetime.now()
        data = []
        for i in range(limit):
            time_point = now - timedelta(minutes=limit-i)
            data.append({
                "timestamp": time_point,
                "soil_moisture": random.uniform(30.0, 60.0),
                "temperature": random.uniform(22.0, 28.0)
            })
        return pd.DataFrame(data)
    
    try:
        req = requests.get(f"{API_URL}/sensors/plants/{plant_id}/history?limit={limit}")
        if req.status_code == 200:
            data = req.json()
            if data:
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values(by="timestamp")
                return df
    except Exception as e:
        st.error(f"Erro ao buscar histórico: {e}")
    return pd.DataFrame()

def set_threshold(plant_id, threshold):
    if USE_MOCK_DATA:
        st.toast(f"✅ Limiar da planta {plant_id} alterado para {threshold}% (Mock)")
        return True
    
    try:
        # Agora chamamos a rota definitiva atrelada à PLANTA, não ao dispositivo
        req = requests.patch(
            f"{API_URL}/plants/{plant_id}/threshold", 
            json={"min_moisture": float(threshold)}
        )
        
        if req.status_code == 200:
            st.toast("✅ Limiar alterado com sucesso na API e enviado para o ESP32!")
            return True
        else:
            st.error(f"Erro na API: {req.text}")
            return False
    except Exception as e:
        st.error(f"Erro de conexão ao salvar: {e}")
        return False

# ==========================================
# Interface de Usuário (UI)
# ==========================================
st.title("🌱 Dashboard - Irrigador Automático")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    
    if USE_MOCK_DATA:
        st.info("⚠️ Rodando com Dados Simulados (Mock)")
    else:
        st.success("🔌 Conectado à API Real")

    devices = get_devices()
    plants = get_plants()
    
    if not devices:
        st.warning("Nenhum dispositivo encontrado.")
        st.stop()
        
    device_options = {d["id"]: f"{d.get('name', 'Disp')} ({d['mqtt_client_id']})" for d in devices}
    selected_device_id = st.selectbox("Selecione o Módulo (ESP32)", options=list(device_options.keys()), format_func=lambda x: device_options[x])
    
    # Fazendo o DE-PARA correto de Device -> Plant
    selected_plant = next((p for p in plants if p.get("device_id") == selected_device_id), None)
    
    st.divider()
    st.subheader("💧 Controle de Irrigação")
    
    if selected_plant:
        # Usa o min_moisture da planta como threshold padrão se existir
        default_threshold = selected_plant["min_moisture"]
        new_threshold = st.slider("Limiar de Umidade (%)", min_value=0, max_value=100, value=int(default_threshold))
        
        if st.button("Salvar Limiar", use_container_width=True):
            set_threshold(selected_plant["id"], new_threshold)
    else:
        st.warning("Este dispositivo não possui uma Planta associada no Banco de Dados.")
        new_threshold = 40

# --- ÁREA PRINCIPAL ---
if not selected_plant:
    st.error("⚠️ Este dispositivo não possui uma Planta associada no Banco de Dados.")
    st.stop()

st.markdown(f"**Visualizando dados da planta:** {selected_plant.get('name', 'Desconhecida')} (ID: {selected_plant['id']})")

df_history = get_history(selected_plant["id"], limit=60)

if df_history.empty:
    st.info("Aguardando leituras do banco de dados para esta planta...")
else:
    current_data = df_history.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    pump_status = "Ligada 💦" if current_data['soil_moisture'] < new_threshold else "Desligada ⏸️"
    pump_color = "normal" if current_data['soil_moisture'] >= new_threshold else "inverse"

    col1.metric("Umidade do Solo", f"{current_data['soil_moisture']:.1f}%", delta=f"Limiar: {new_threshold}%", delta_color="off")
    col2.metric("Temperatura", f"{current_data['temperature']:.1f} °C")
    col3.metric("Status da Bomba", pump_status, delta="Automático", delta_color=pump_color)

    st.divider()
    st.subheader("📈 Histórico Recente")
    
    tab1, tab2 = st.tabs(["Umidade do Solo", "Temperatura"])
    
    with tab1:
        df_chart_hum = df_history[['timestamp', 'soil_moisture']].set_index('timestamp')
        df_chart_hum['Limiar'] = new_threshold
        st.line_chart(df_chart_hum, color=["#2f9e5b", "#cc4b37"])
        
    with tab2:
        df_chart_temp = df_history[['timestamp', 'temperature']].set_index('timestamp')
        st.line_chart(df_chart_temp, color=["#d9971f"])

if st.button("Atualizar Dados Agora 🔄"):
    st.rerun()