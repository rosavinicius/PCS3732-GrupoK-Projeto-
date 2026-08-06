import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime, timedelta

# ==========================================
# Configurações da Página e Variáveis Globais
# ==========================================
st.set_page_config(page_title="Irrigador Automático", page_icon="🌱", layout="wide")

# URL do seu backend no Raspberry Pi (ajuste conforme necessário)
API_URL = "http://localhost:8000"

# Flag para usar dados simulados caso o backend ainda não esteja pronto
# Mude para False quando o ESP32 e o backend estiverem comunicando perfeitamente.
USE_MOCK_DATA = True 

# ==========================================
# Funções de Comunicação com a API / Mocks
# ==========================================
def get_devices():
    if USE_MOCK_DATA:
        return [{"id": "ESP32_01", "name": "Horta (Tomates)", "status": "online", "humidityThreshold": 40}]
    try:
        return requests.get(f"{API_URL}/devices").json()
    except:
        return []

def get_history(device_id, minutes=60):
    if USE_MOCK_DATA:
        # Gera dados falsos para demonstração
        now = datetime.now()
        data = []
        for i in range(minutes):
            time_point = now - timedelta(minutes=minutes-i)
            data.append({
                "timestamp": time_point,
                "humidity": random.uniform(30, 60),
                "temperature": random.uniform(22, 28),
                "ph": random.uniform(6.0, 7.0)
            })
        return pd.DataFrame(data)
    try:
        req = requests.get(f"{API_URL}/devices/{device_id}/history?minutes={minutes}").json()
        df = pd.DataFrame(req)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

def set_threshold(device_id, threshold):
    if USE_MOCK_DATA:
        st.toast(f"✅ Limiar do {device_id} alterado para {threshold}% (Mock)")
        return True
    try:
        requests.post(f"{API_URL}/devices/{device_id}/config", json={"humidityThreshold": threshold})
        st.toast(f"✅ Limiar alterado com sucesso!")
        return True
    except:
        st.error("Erro ao comunicar com o Raspberry Pi.")
        return False

# ==========================================
# Interface de Usuário (UI)
# ==========================================
st.title("🌱 Dashboard - Irrigador Automático")
st.markdown("Monitoramento de umidade do solo para evitar subirrigação e superirrigação.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    devices = get_devices()
    
    if not devices:
        st.warning("Nenhum dispositivo ESP32 encontrado.")
        st.stop()
        
    device_options = {d["id"]: f"{d.get('name', 'Dispositivo')} ({d['id']})" for d in devices}
    selected_device_id = st.selectbox("Selecione o Módulo", options=list(device_options.keys()), format_func=lambda x: device_options[x])
    
    selected_device = next(d for d in devices if d["id"] == selected_device_id)
    
    st.divider()
    st.subheader("💧 Controle de Irrigação")
    # RF-3: Definição de Limiar para Irrigação
    new_threshold = st.slider(
        "Limiar de Umidade (%)", 
        min_value=0, max_value=100, 
        value=selected_device.get("humidityThreshold", 40),
        help="A bomba será acionada se a umidade cair abaixo deste valor."
    )
    
    if st.button("Salvar Limiar", use_container_width=True):
        set_threshold(selected_device_id, new_threshold)

    st.divider()
    st.markdown("### 👨‍💻 Autores (PCS3732)")
    st.markdown("- André Yugo Inoue\n- Beatriz Barreto Tavora\n- João Victor M. Milanezi\n- Vinícius de Andrade Rosa")

# --- ÁREA PRINCIPAL ---
# Busca o histórico do dispositivo selecionado
df_history = get_history(selected_device_id, minutes=60)

if df_history.empty:
    st.info("Aguardando leituras dos sensores...")
else:
    # Pegando as últimas leituras
    current_data = df_history.iloc[-1]
    
    # RF-1, RF-2, RF-4, RF-5: Visualização do Estado do Sistema
    col1, col2, col3, col4 = st.columns(4)
    
    # Lógica simples para indicar se a bomba deveria estar ligada
    pump_status = "Ligada 💦" if current_data['humidity'] < new_threshold else "Desligada ⏸️"
    pump_color = "normal" if current_data['humidity'] >= new_threshold else "inverse"

    col1.metric("Umidade do Solo", f"{current_data['humidity']:.1f}%", delta=f"Limiar: {new_threshold}%", delta_color="off")
    col2.metric("Temperatura", f"{current_data['temperature']:.1f} °C")
    col3.metric("pH Estimado", f"{current_data['ph']:.1f}")
    col4.metric("Status da Bomba", pump_status, delta="Automático", delta_color=pump_color)

    st.divider()
    
    # RF-6: Visualização de Série Temporal
    st.subheader("📈 Histórico Recente (Última Hora)")
    
    tab1, tab2 = st.tabs(["Umidade do Solo", "Temperatura"])
    
    with tab1:
        # Plota a umidade juntamente com uma linha indicando o limiar atual
        df_chart_hum = df_history[['timestamp', 'humidity']].set_index('timestamp')
        df_chart_hum['Limiar'] = new_threshold
        st.line_chart(df_chart_hum, color=["#2f9e5b", "#cc4b37"])
        
    with tab2:
        df_chart_temp = df_history[['timestamp', 'temperature']].set_index('timestamp')
        st.line_chart(df_chart_temp, color=["#d9971f"])

# Atualiza a página a cada X segundos automaticamente (opcional)
time_refresh = st.empty()
if st.button("Atualizar Dados Agora 🔄"):
    st.rerun()