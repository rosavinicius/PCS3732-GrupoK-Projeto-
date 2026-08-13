import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime, timedelta


# ==========================================
# Configurações
# ==========================================

st.set_page_config(
    page_title="Irrigador Automático",
    page_icon="🌱",
    layout="wide"
)

API_URL = "http://localhost:8000"

# False = usa API real
# True = usa dados simulados
USE_MOCK_DATA = False


# ==========================================
# Funções de Comunicação com a API
# ==========================================

def get_devices():
    """Busca os dispositivos ESP32 cadastrados."""

    if USE_MOCK_DATA:
        return [
            {
                "id": 1,
                "name": "ESP32 Horta",
                "mqtt_client_id": "esp32-vaso-01"
            },
            {
                "id": 2,
                "name": "ESP32 Estufa",
                "mqtt_client_id": "esp32-estufa-02"
            }
        ]

    try:
        req = requests.get(
            f"{API_URL}/devices/",
            timeout=5
        )

        if req.status_code == 200:
            data = req.json()

            if isinstance(data, list):
                return [
                    device
                    for device in data
                    if isinstance(device, dict)
                ]

            st.sidebar.error(
                "A API retornou um formato inválido para devices."
            )

    except requests.exceptions.RequestException as e:
        st.sidebar.error(
            f"Erro ao conectar com API de Devices: {e}"
        )

    return []


def get_plants():
    """Busca as plantas cadastradas."""

    if USE_MOCK_DATA:
        return [
            {
                "id": 10,
                "device_id": 1,
                "name": "Tomates",
                "min_moisture": 40.0,
                "max_moisture": 80.0
            },
            {
                "id": 20,
                "device_id": 2,
                "name": "Orquídeas",
                "min_moisture": 50.0,
                "max_moisture": 70.0
            }
        ]

    try:
        req = requests.get(
            f"{API_URL}/plants/",
            timeout=5
        )

        if req.status_code == 200:
            data = req.json()

            if isinstance(data, list):
                return [
                    plant
                    for plant in data
                    if isinstance(plant, dict)
                ]

            st.sidebar.error(
                "A API retornou um formato inválido para plants."
            )

    except requests.exceptions.RequestException as e:
        st.sidebar.error(
            f"Erro ao conectar com API de Plants: {e}"
        )

    return []


def get_history(plant_id, limit=60):
    """Busca o histórico de sensores de uma planta."""

    if USE_MOCK_DATA:
        now = datetime.now()

        data = []

        for i in range(limit):
            time_point = now - timedelta(
                minutes=limit - i
            )

            data.append({
                "timestamp": time_point,
                "soil_moisture": random.uniform(30.0, 60.0),
                "temperature": random.uniform(22.0, 28.0)
            })

        return pd.DataFrame(data)

    try:
        req = requests.get(
            f"{API_URL}/sensors/plants/{plant_id}/history",
            params={"limit": limit},
            timeout=5
        )

        if req.status_code == 200:
            data = req.json()

            if not data:
                return pd.DataFrame()

            if not isinstance(data, list):
                st.error(
                    "A API retornou um formato inválido para o histórico."
                )
                return pd.DataFrame()

            df = pd.DataFrame(data)

            # Verifica se as colunas necessárias existem
            required_columns = [
                "timestamp",
                "soil_moisture",
                "temperature"
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in df.columns
            ]

            if missing_columns:
                st.error(
                    "Dados do histórico incompletos. "
                    f"Colunas ausentes: {missing_columns}"
                )
                return pd.DataFrame()

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

            df["soil_moisture"] = pd.to_numeric(
                df["soil_moisture"],
                errors="coerce"
            )

            df["temperature"] = pd.to_numeric(
                df["temperature"],
                errors="coerce"
            )

            df = df.dropna(
                subset=[
                    "timestamp",
                    "soil_moisture",
                    "temperature"
                ]
            )

            df = df.sort_values(
                by="timestamp"
            )

            return df

        else:
            st.error(
                f"Erro ao buscar histórico. "
                f"HTTP {req.status_code}: {req.text}"
            )

    except requests.exceptions.RequestException as e:
        st.error(
            f"Erro ao buscar histórico: {e}"
        )

    return pd.DataFrame()


def set_threshold(plant_id, threshold):
    """Altera o limiar mínimo de umidade da planta."""

    if USE_MOCK_DATA:
        st.toast(
            f"✅ Limiar da planta {plant_id} "
            f"alterado para {threshold}% (Mock)"
        )
        return True

    try:
        req = requests.patch(
            f"{API_URL}/plants/{plant_id}/threshold",
            json={
                "min_moisture": float(threshold)
            },
            timeout=5
        )

        if req.status_code == 200:
            st.toast(
                "✅ Limiar alterado com sucesso!"
            )
            return True

        else:
            st.error(
                f"Erro na API: HTTP {req.status_code}\n\n"
                f"{req.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        st.error(
            f"Erro de conexão ao salvar: {e}"
        )
        return False


# ==========================================
# Interface
# ==========================================

st.title("🌱 Dashboard - Irrigador Automático")


# ==========================================
# Barra Lateral
# ==========================================

selected_plant = None
new_threshold = 40

with st.sidebar:

    st.header("⚙️ Configurações")

    if USE_MOCK_DATA:
        st.info(
            "⚠️ Rodando com Dados Simulados (Mock)"
        )
    else:
        st.success(
            "🔌 Conectado à API Real"
        )

    # --------------------------------------
    # Buscar dispositivos
    # --------------------------------------

    devices = get_devices()

    if not devices:
        st.warning(
            "Nenhum dispositivo encontrado."
        )
        st.stop()

    # Remove dispositivos inválidos
    valid_devices = [
        device
        for device in devices
        if isinstance(device, dict)
        and device.get("id") is not None
    ]

    if not valid_devices:
        st.error(
            "A API não retornou dispositivos válidos."
        )
        st.stop()

    # --------------------------------------
    # Buscar plantas
    # --------------------------------------

    plants = get_plants()

    # --------------------------------------
    # Montar opções de dispositivos
    # --------------------------------------

    device_options = {}

    for device in valid_devices:

        device_id = device["id"]

        device_name = device.get(
            "name",
            "Dispositivo"
        )

        mqtt_client_id = device.get(
            "mqtt_client_id",
            "sem MQTT ID"
        )

        device_options[device_id] = (
            f"{device_name} ({mqtt_client_id})"
        )

    # --------------------------------------
    # Seleção do ESP32
    # --------------------------------------

    selected_device_id = st.selectbox(
        "Selecione o Módulo (ESP32)",
        options=list(device_options.keys()),
        format_func=lambda x: device_options[x]
    )

    # --------------------------------------
    # Encontrar planta associada
    # --------------------------------------

    selected_plant = next(
        (
            plant
            for plant in plants
            if isinstance(plant, dict)
            and plant.get("device_id") == selected_device_id
        ),
        None
    )

    # --------------------------------------
    # Debug opcional
    # --------------------------------------

    # Se quiser investigar o retorno da API,
    # descomente as linhas abaixo.

    # st.write("Devices:", devices)
    # st.write("Plants:", plants)
    # st.write("Selected device:", selected_device_id)
    # st.write("Selected plant:", selected_plant)

    st.divider()

    st.subheader(
        "💧 Controle de Irrigação"
    )

    # ======================================
    # Planta encontrada
    # ======================================

    if selected_plant is not None:

        plant_id = selected_plant.get("id")

        plant_name = selected_plant.get(
            "name",
            "Desconhecida"
        )

        min_moisture = selected_plant.get(
            "min_moisture",
            40
        )

        # ----------------------------------
        # Validação do ID
        # ----------------------------------

        if plant_id is None:

            st.error(
                "⚠️ A planta associada não possui ID."
            )

            st.stop()

        # ----------------------------------
        # Validação do threshold
        # ----------------------------------

        try:
            default_threshold = int(
                float(min_moisture)
            )
        except (TypeError, ValueError):
            default_threshold = 40

        # Garante que está entre 0 e 100
        default_threshold = max(
            0,
            min(100, default_threshold)
        )

        # ----------------------------------
        # Slider
        # ----------------------------------

        new_threshold = st.slider(
            "Limiar de Umidade (%)",
            min_value=0,
            max_value=100,
            value=default_threshold
        )

        # ----------------------------------
        # Salvar threshold
        # ----------------------------------

        if st.button(
            "Salvar Limiar",
            use_container_width=True
        ):

            set_threshold(
                plant_id,
                new_threshold
            )

    # ======================================
    # Nenhuma planta encontrada
    # ======================================

    else:

        st.warning(
            "Este dispositivo não possui "
            "uma Planta associada no Banco de Dados."
        )

        new_threshold = 40


# ==========================================
# Área Principal
# ==========================================

# IMPORTANTE:
# Aqui fazemos a verificação ANTES de qualquer
# selected_plant.get(...)

if selected_plant is None:

    st.error(
        "⚠️ Este dispositivo não possui "
        "uma Planta associada no Banco de Dados."
    )

    st.info(
        "Verifique se o campo 'device_id' da planta "
        "corresponde ao 'id' do ESP32 selecionado."
    )

    st.stop()


# ==========================================
# Dados seguros da planta
# ==========================================

plant_id = selected_plant.get("id")

plant_name = selected_plant.get(
    "name",
    "Desconhecida"
)


# Validação final
if plant_id is None:

    st.error(
        "⚠️ A planta selecionada não possui um ID válido."
    )

    st.stop()


# ==========================================
# Título da planta
# ==========================================

st.markdown(
    f"**Visualizando dados da planta:** "
    f"{plant_name} "
    f"(ID: {plant_id})"
)


# ==========================================
# Histórico
# ==========================================

df_history = get_history(
    plant_id,
    limit=60
)


# ==========================================
# Sem dados
# ==========================================

if df_history.empty:

    st.info(
        "Aguardando leituras do banco de dados "
        "para esta planta..."
    )


# ==========================================
# Com dados
# ==========================================

else:

    current_data = df_history.iloc[-1]

    # --------------------------------------
    # Dados atuais
    # --------------------------------------

    current_moisture = float(
        current_data["soil_moisture"]
    )

    current_temperature = float(
        current_data["temperature"]
    )

    # --------------------------------------
    # Status da bomba
    # --------------------------------------

    if current_moisture < new_threshold:

        pump_status = "Ligada 💦"
        pump_color = "inverse"

    else:

        pump_status = "Desligada ⏸️"
        pump_color = "normal"

    # --------------------------------------
    # Cards
    # --------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Umidade do Solo",
        f"{current_moisture:.1f}%",
        delta=f"Limiar: {new_threshold}%",
        delta_color="off"
    )

    col2.metric(
        "Temperatura",
        f"{current_temperature:.1f} °C"
    )

    col3.metric(
        "Status da Bomba",
        pump_status,
        delta="Automático",
        delta_color=pump_color
    )

    # --------------------------------------
    # Histórico
    # --------------------------------------

    st.divider()

    st.subheader(
        "📈 Histórico Recente"
    )

    tab1, tab2 = st.tabs(
        [
            "Umidade do Solo",
            "Temperatura"
        ]
    )

    # ======================================
    # Gráfico de Umidade
    # ======================================

    with tab1:

        df_chart_hum = df_history[
            [
                "timestamp",
                "soil_moisture"
            ]
        ].copy()

        df_chart_hum = (
            df_chart_hum
            .set_index("timestamp")
        )

        df_chart_hum["Limiar"] = new_threshold

        st.line_chart(
            df_chart_hum,
            color=[
                "#2f9e5b",
                "#cc4b37"
            ]
        )

    # ======================================
    # Gráfico de Temperatura
    # ======================================

    with tab2:

        df_chart_temp = df_history[
            [
                "timestamp",
                "temperature"
            ]
        ].copy()

        df_chart_temp = (
            df_chart_temp
            .set_index("timestamp")
        )

        st.line_chart(
            df_chart_temp,
            color=["#d9971f"]
        )


# ==========================================
# Atualizar dados
# ==========================================

if st.button(
    "Atualizar Dados Agora 🔄"
):

    st.rerun()
    