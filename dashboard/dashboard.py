import streamlit as st
import pandas as pd
import requests
import random

from datetime import datetime, timedelta


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Irrigador Automático",
    page_icon="🌱",
    layout="wide"
)


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

API_URL = "http://localhost:8000"

# False = usa API real
# True = usa dados simulados
USE_MOCK_DATA = False

REQUEST_TIMEOUT = 5


# ============================================================
# FUNÇÕES AUXILIARES DE VALIDAÇÃO
# ============================================================

def is_valid_dict(value):
    """
    Verifica se o valor é um dicionário válido.
    """

    return isinstance(value, dict)


def safe_float(value, default=None):
    """
    Converte um valor para float com segurança.
    """

    if value is None:
        return default

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def safe_int(value, default=None):
    """
    Converte um valor para int com segurança.
    """

    if value is None:
        return default

    try:
        return int(float(value))

    except (TypeError, ValueError):
        return default


def normalize_list(data):
    """
    Garante que o retorno da API seja uma lista de dicionários.

    Exemplos:

    None
        -> []

    {}
        -> []

    [{"id": 1}, None]
        -> [{"id": 1}]

    [{"id": 1}]
        -> [{"id": 1}]
    """

    if data is None:
        return []

    if not isinstance(data, list):
        return []

    return [
        item
        for item in data
        if isinstance(item, dict)
    ]


# ============================================================
# API - DEVICES
# ============================================================

def get_devices():

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

        response = requests.get(
            f"{API_URL}/devices/",
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:

            st.sidebar.error(
                f"Erro ao buscar dispositivos. "
                f"HTTP {response.status_code}"
            )

            return []

        data = response.json()

        return normalize_list(data)

    except requests.exceptions.RequestException as e:

        st.sidebar.error(
            f"Erro de conexão com a API de Devices: {e}"
        )

        return []

    except ValueError:

        st.sidebar.error(
            "A API de Devices retornou um JSON inválido."
        )

        return []

    except Exception as e:

        st.sidebar.error(
            f"Erro inesperado ao buscar Devices: {e}"
        )

        return []


# ============================================================
# API - PLANTS
# ============================================================

def get_plants():

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

        response = requests.get(
            f"{API_URL}/plants/",
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:

            st.sidebar.error(
                f"Erro ao buscar plantas. "
                f"HTTP {response.status_code}"
            )

            return []

        data = response.json()

        return normalize_list(data)

    except requests.exceptions.RequestException as e:

        st.sidebar.error(
            f"Erro de conexão com a API de Plants: {e}"
        )

        return []

    except ValueError:

        st.sidebar.error(
            "A API de Plants retornou um JSON inválido."
        )

        return []

    except Exception as e:

        st.sidebar.error(
            f"Erro inesperado ao buscar Plants: {e}"
        )

        return []


# ============================================================
# API - HISTÓRICO
# ============================================================

def get_history(plant_id, limit=60):

    # --------------------------------------------------------
    # Proteção contra ID inválido
    # --------------------------------------------------------

    if plant_id is None:

        return pd.DataFrame()

    if USE_MOCK_DATA:

        now = datetime.now()

        data = []

        for i in range(limit):

            time_point = (
                now
                - timedelta(minutes=limit - i)
            )

            data.append(
                {
                    "timestamp": time_point,
                    "soil_moisture": random.uniform(
                        30.0,
                        60.0
                    ),
                    "temperature": random.uniform(
                        22.0,
                        28.0
                    )
                }
            )

        return pd.DataFrame(data)

    try:

        response = requests.get(
            f"{API_URL}/sensors/plants/{plant_id}/history",
            params={"limit": limit},
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code != 200:

            st.error(
                f"Erro ao buscar histórico da planta "
                f"{plant_id}. "
                f"HTTP {response.status_code}"
            )

            return pd.DataFrame()

        data = response.json()

        # ----------------------------------------------------
        # API retornou None
        # ----------------------------------------------------

        if data is None:

            return pd.DataFrame()

        # ----------------------------------------------------
        # API não retornou uma lista
        # ----------------------------------------------------

        if not isinstance(data, list):

            st.error(
                "A API de histórico retornou um formato inválido."
            )

            return pd.DataFrame()

        # ----------------------------------------------------
        # Remove registros None
        # ----------------------------------------------------

        data = [
            item
            for item in data
            if isinstance(item, dict)
        ]

        if not data:

            return pd.DataFrame()

        df = pd.DataFrame(data)

        # ----------------------------------------------------
        # Verificar colunas
        # ----------------------------------------------------

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
                "Os dados de histórico estão incompletos. "
                f"Colunas ausentes: {missing_columns}"
            )

            return pd.DataFrame()

        # ----------------------------------------------------
        # Converter timestamp
        # ----------------------------------------------------

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        # ----------------------------------------------------
        # Converter sensores
        # ----------------------------------------------------

        df["soil_moisture"] = pd.to_numeric(
            df["soil_moisture"],
            errors="coerce"
        )

        df["temperature"] = pd.to_numeric(
            df["temperature"],
            errors="coerce"
        )

        # ----------------------------------------------------
        # Remover linhas inválidas
        # ----------------------------------------------------

        df = df.dropna(
            subset=[
                "timestamp",
                "soil_moisture",
                "temperature"
            ]
        )

        if df.empty:

            return pd.DataFrame()

        # ----------------------------------------------------
        # Ordenar
        # ----------------------------------------------------

        df = df.sort_values(
            by="timestamp"
        )

        return df

    except requests.exceptions.RequestException as e:

        st.error(
            f"Erro de conexão ao buscar histórico: {e}"
        )

        return pd.DataFrame()

    except ValueError:

        st.error(
            "A API de histórico retornou JSON inválido."
        )

        return pd.DataFrame()

    except Exception as e:

        st.error(
            f"Erro inesperado ao buscar histórico: {e}"
        )

        return pd.DataFrame()


# ============================================================
# API - ALTERAR THRESHOLD
# ============================================================

def set_threshold(plant_id, threshold):

    # --------------------------------------------------------
    # Validação
    # --------------------------------------------------------

    if plant_id is None:

        st.error(
            "Não é possível alterar o limiar: "
            "a planta não possui ID."
        )

        return False

    threshold = safe_float(
        threshold,
        None
    )

    if threshold is None:

        st.error(
            "Valor de limiar inválido."
        )

        return False

    threshold = max(
        0.0,
        min(100.0, threshold)
    )

    # --------------------------------------------------------
    # Mock
    # --------------------------------------------------------

    if USE_MOCK_DATA:

        st.toast(
            f"✅ Limiar da planta {plant_id} "
            f"alterado para {threshold:.0f}% (Mock)"
        )

        return True

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    try:

        response = requests.patch(
            f"{API_URL}/plants/{plant_id}/threshold",
            json={
                "min_moisture": threshold
            },
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 200:

            st.toast(
                "✅ Limiar alterado com sucesso!"
            )

            return True

        st.error(
            f"Erro ao alterar limiar. "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

        return False

    except requests.exceptions.RequestException as e:

        st.error(
            f"Erro de conexão ao salvar limiar: {e}"
        )

        return False

    except Exception as e:

        st.error(
            f"Erro inesperado ao salvar limiar: {e}"
        )

        return False


# ============================================================
# INÍCIO DA INTERFACE
# ============================================================

st.title(
    "🌱 Dashboard - Irrigador Automático"
)


# ============================================================
# VARIÁVEIS PADRÃO
# ============================================================

selected_plant = None
selected_device_id = None
new_threshold = 40


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Configurações"
    )

    # --------------------------------------------------------
    # Status da API
    # --------------------------------------------------------

    if USE_MOCK_DATA:

        st.info(
            "⚠️ Rodando com Dados Simulados (Mock)"
        )

    else:

        st.success(
            "🔌 Usando API Real"
        )

    # --------------------------------------------------------
    # Buscar dispositivos
    # --------------------------------------------------------

    devices = get_devices()

    if not devices:

        st.warning(
            "Nenhum dispositivo encontrado no banco de dados."
        )

        st.info(
            "Verifique se existem dispositivos cadastrados "
            "na tabela de devices."
        )

        st.stop()

    # --------------------------------------------------------
    # Filtrar dispositivos válidos
    # --------------------------------------------------------

    valid_devices = []

    for device in devices:

        if not isinstance(device, dict):
            continue

        device_id = device.get("id")

        if device_id is None:
            continue

        valid_devices.append(device)

    if not valid_devices:

        st.error(
            "Existem dispositivos no banco, "
            "mas nenhum possui um ID válido."
        )

        st.stop()

    # --------------------------------------------------------
    # Montar opções
    # --------------------------------------------------------

    device_options = {}

    for device in valid_devices:

        device_id = device.get("id")

        name = device.get(
            "name",
            "Dispositivo"
        )

        mqtt_client_id = device.get(
            "mqtt_client_id",
            "MQTT não configurado"
        )

        if name is None:
            name = "Dispositivo"

        if mqtt_client_id is None:
            mqtt_client_id = "MQTT não configurado"

        device_options[device_id] = (
            f"{name} ({mqtt_client_id})"
        )

    # --------------------------------------------------------
    # Seleção do dispositivo
    # --------------------------------------------------------

    selected_device_id = st.selectbox(
        "Selecione o Módulo (ESP32)",
        options=list(device_options.keys()),
        format_func=lambda device_id: device_options.get(
            device_id,
            f"Dispositivo {device_id}"
        )
    )

    # --------------------------------------------------------
    # Buscar plantas
    # --------------------------------------------------------

    plants = get_plants()

    if not plants:

        st.warning(
            "Nenhuma planta encontrada no banco de dados."
        )

        st.info(
            "Cadastre pelo backend uma planta que tenha `device_id` "
            "igual ao ID de um dispositivo existente."
        )

        st.stop()

    # --------------------------------------------------------
    # Encontrar planta associada
    # --------------------------------------------------------

    selected_plant = None

    if plants:

        for plant in plants:

            # Proteção contra None
            if not isinstance(plant, dict):
                continue

            plant_device_id = plant.get(
                "device_id"
            )

            # Se não possui device_id,
            # não conseguimos associá-la ao ESP32
            if plant_device_id is None:
                continue

            # Comparação
            if plant_device_id == selected_device_id:

                # Verifica se a planta possui ID
                if plant.get("id") is not None:

                    selected_plant = plant

                break

    # --------------------------------------------------------
    # Controle da planta
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "💧 Controle de Irrigação"
    )

    if isinstance(selected_plant, dict):

        # ------------------------------------
        # ID
        # ------------------------------------

        plant_id = selected_plant.get(
            "id"
        )

        if plant_id is None:

            st.error(
                "A planta encontrada não possui ID."
            )

            selected_plant = None

        else:

            # --------------------------------
            # Nome
            # --------------------------------

            plant_name = selected_plant.get(
                "name"
            )

            if plant_name is None:
                plant_name = "Planta desconhecida"

            # --------------------------------
            # Threshold
            # --------------------------------

            min_moisture = selected_plant.get(
                "min_moisture"
            )

            min_moisture = safe_float(
                min_moisture,
                40.0
            )

            # Garantir intervalo
            min_moisture = max(
                0.0,
                min(100.0, min_moisture)
            )

            default_threshold = int(
                min_moisture
            )

            # --------------------------------
            # Slider
            # --------------------------------

            new_threshold = st.slider(
                "Limiar de Umidade (%)",
                min_value=0,
                max_value=100,
                value=default_threshold
            )

            # --------------------------------
            # Salvar
            # --------------------------------

            if st.button(
                "Salvar Limiar",
                use_container_width=True
            ):

                success = set_threshold(
                    plant_id,
                    new_threshold
                )

                if success:

                    st.rerun()

    # --------------------------------------------------------
    # Sem planta
    # --------------------------------------------------------

    if selected_plant is None:

        st.warning(
            "Este dispositivo não possui "
            "uma Planta associada."
        )

        st.caption(
            "A planta precisa possuir um "
            "`device_id` correspondente ao ID "
            "do ESP32."
        )

        new_threshold = 40


# ============================================================
# ÁREA PRINCIPAL
# ============================================================

# ============================================================
# PROTEÇÃO ABSOLUTA CONTRA selected_plant = None
# ============================================================

if not isinstance(
    selected_plant,
    dict
):

    st.error(
        "⚠️ Nenhuma planta válida está associada "
        "ao dispositivo selecionado."
    )

    st.info(
        "Verifique no banco de dados se existe uma planta "
        "com `device_id` igual ao `id` do dispositivo."
    )

    # Mostrar informações úteis para diagnóstico
    with st.expander(
        "🔎 Diagnóstico"
    ):

        st.write(
            "ID do dispositivo selecionado:",
            selected_device_id
        )

        st.write(
            "Quantidade de dispositivos:",
            len(devices)
            if isinstance(devices, list)
            else 0
        )

        st.write(
            "Quantidade de plantas:",
            len(plants)
            if isinstance(plants, list)
            else 0
        )

    st.stop()


# ============================================================
# AGORA selected_plant É GARANTIDAMENTE UM DICT
# ============================================================

plant_id = safe_int(
    (
        selected_plant.get("id")
        if isinstance(selected_plant, dict)
        else None
    ),
    None
)

if plant_id is None:

    st.error(
        "⚠️ A planta selecionada não possui ID."
    )

    st.stop()

plant_name = (
    selected_plant.get("name")
    if isinstance(selected_plant, dict)
    else None
)

if plant_name is None:

    plant_name = "Planta desconhecida"


# ============================================================
# CABEÇALHO DA PLANTA
# ============================================================

st.markdown(
    f"**Visualizando dados da planta:** "
    f"{plant_name} "
    f"(ID: {plant_id})"
)


# ============================================================
# HISTÓRICO
# ============================================================

df_history = get_history(
    plant_id,
    limit=60
)


# ============================================================
# SEM DADOS DE SENSOR
# ============================================================

if not isinstance(
    df_history,
    pd.DataFrame
):

    st.error(
        "O histórico retornado pela API "
        "não é um DataFrame válido."
    )

    st.stop()


if df_history.empty:

    st.info(
        "Aguardando leituras dos sensores "
        "para esta planta."
    )

    st.caption(
        "Isso pode acontecer quando a planta ainda "
        "não possui leituras registradas no banco."
    )

else:

    # ========================================================
    # VALIDAR DADOS DA ÚLTIMA LEITURA
    # ========================================================

    required_columns = [
        "timestamp",
        "soil_moisture",
        "temperature"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df_history.columns
    ]

    if missing_columns:

        st.error(
            "O histórico não possui todas as colunas "
            f"necessárias: {missing_columns}"
        )

        st.stop()

    # ========================================================
    # ÚLTIMA LEITURA
    # ========================================================

    current_data = df_history.iloc[-1]

    # --------------------------------------------------------
    # Umidade
    # --------------------------------------------------------

    current_moisture = safe_float(
        current_data.get(
            "soil_moisture"
        )
    )

    # --------------------------------------------------------
    # Temperatura
    # --------------------------------------------------------

    current_temperature = safe_float(
        current_data.get(
            "temperature"
        )
    )

    # --------------------------------------------------------
    # Threshold atual
    # --------------------------------------------------------

    threshold = safe_float(
        new_threshold,
        40.0
    )

    threshold = max(
        0.0,
        min(100.0, threshold)
    )

    # ========================================================
    # CARDS
    # ========================================================

    col1, col2, col3 = st.columns(3)

    # --------------------------------------------------------
    # Umidade
    # --------------------------------------------------------

    if current_moisture is None:

        col1.metric(
            "Umidade do Solo",
            "Sem dados"
        )

    else:

        col1.metric(
            "Umidade do Solo",
            f"{current_moisture:.1f}%",
            delta=f"Limiar: {threshold:.0f}%",
            delta_color="off"
        )

    # --------------------------------------------------------
    # Temperatura
    # --------------------------------------------------------

    if current_temperature is None:

        col2.metric(
            "Temperatura",
            "Sem dados"
        )

    else:

        col2.metric(
            "Temperatura",
            f"{current_temperature:.1f} °C"
        )

    # --------------------------------------------------------
    # Status da bomba
    # --------------------------------------------------------

    if current_moisture is None:

        pump_status = "Indisponível ⚠️"
        pump_color = "off"

    elif current_moisture < threshold:

        pump_status = "Ligada 💦"
        pump_color = "inverse"

    else:

        pump_status = "Desligada ⏸️"
        pump_color = "normal"

    col3.metric(
        "Status da Bomba",
        pump_status,
        delta="Automático"
    )

    # ========================================================
    # HISTÓRICO
    # ========================================================

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

    # ========================================================
    # GRÁFICO DE UMIDADE
    # ========================================================

    with tab1:

        df_chart_hum = df_history[
            [
                "timestamp",
                "soil_moisture"
            ]
        ].copy()

        df_chart_hum = df_chart_hum.dropna(
            subset=[
                "timestamp",
                "soil_moisture"
            ]
        )

        if df_chart_hum.empty:

            st.info(
                "Não existem dados válidos "
                "de umidade para exibir."
            )

        else:

            df_chart_hum = (
                df_chart_hum
                .set_index("timestamp")
            )

            df_chart_hum["Limiar"] = threshold

            st.line_chart(
                df_chart_hum,
                color=[
                    "#2f9e5b",
                    "#cc4b37"
                ]
            )

    # ========================================================
    # GRÁFICO DE TEMPERATURA
    # ========================================================

    with tab2:

        df_chart_temp = df_history[
            [
                "timestamp",
                "temperature"
            ]
        ].copy()

        df_chart_temp = df_chart_temp.dropna(
            subset=[
                "timestamp",
                "temperature"
            ]
        )

        if df_chart_temp.empty:

            st.info(
                "Não existem dados válidos "
                "de temperatura para exibir."
            )

        else:

            df_chart_temp = (
                df_chart_temp
                .set_index("timestamp")
            )

            st.line_chart(
                df_chart_temp,
                color=["#d9971f"]
            )


# ============================================================
# BOTÃO DE ATUALIZAÇÃO
# ============================================================

st.divider()

if st.button(
    "Atualizar Dados Agora 🔄",
    use_container_width=True
):

    st.rerun()