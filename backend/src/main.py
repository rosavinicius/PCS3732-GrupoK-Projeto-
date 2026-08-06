import json
import logging
import paho.mqtt.client as mqtt

from backend.src.crud.sensors import create_sensor_reading
from backend.src.db.database import SessionLocal
from backend.src.db.schemas import SensorReadingCreate

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

# -------------------------------------------------------------------
# CONFIGURAÇÕES MQTT
# -------------------------------------------------------------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_SUBSCRIBE_ALL = "devices/+/+"  # Captura sensors, status, pump e config

# -------------------------------------------------------------------
# PERSISTÊNCIA NO BANCO DE DADOS
# -------------------------------------------------------------------
def salvar_no_banco(planta_id: int, umidade: float, temperatura: float):
    """Cria a sessão do banco e grava a leitura enviada pelo ESP32."""
    db = SessionLocal()
    try:
        reading = SensorReadingCreate(
            plant_id=planta_id,
            soil_moisture=umidade,
            temperature=temperatura
        )
        leitura_criada = create_sensor_reading(db=db, reading=reading)
        logging.info(
            f"--> [DB] Sucesso! ESP ID: {planta_id} | "
            f"Umidade: {umidade}% | Temp: {temperatura}°C"
        )
        return leitura_criada
    except Exception as e:
        db.rollback()
        logging.error(f"--> [DB] Erro ao salvar leitura no banco: {e}")
    finally:
        db.close()

# -------------------------------------------------------------------
# ENVIO DE CONFIGURAÇÃO (Raspberry -> ESP32)
# -------------------------------------------------------------------
def enviar_novo_limite_umidade(client: mqtt.Client, device_id: str, humidity_threshold: float):
    """
    Publica o novo limite de umidade no tópico /config respeitando a chave
    esperada pelo ESP32: {"humidityThreshold": float}
    """
    topic = f"devices/{device_id}/config"
    payload = json.dumps({"humidityThreshold": float(humidity_threshold)})
    
    # retained=True garante que o ESP receba caso esteja offline na hora do envio
    client.publish(topic, payload, qos=1, retain=True)
    logging.info(f"--> [CONFIG] Limite enviado para [{topic}]: {payload}")

# -------------------------------------------------------------------
# CALLBACKS DO MQTT
# -------------------------------------------------------------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info(f"Conectado ao Broker MQTT ({MQTT_BROKER}:{MQTT_PORT})")
        client.subscribe(TOPIC_SUBSCRIBE_ALL)
        logging.info(f"Inscrito na árvore de tópicos: {TOPIC_SUBSCRIBE_ALL}")
    else:
        logging.error(f"Falha ao conectar ao Broker MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    try:
        # Ex: msg.topic = "devices/1/sensors"
        topic_parts = msg.topic.split('/')
        if len(topic_parts) != 3 or topic_parts[0] != "devices":
            return

        device_id_str = topic_parts[1]
        subtopic = topic_parts[2]
        payload_str = msg.payload.decode('utf-8')

        # O schema exige plant_id como INT
        try:
            device_id = int(device_id_str)
        except ValueError:
            logging.warning(f"ID do dispositivo ({device_id_str}) precisa ser numérico.")
            return

        # ---------------------------------------------------------------
        # 1. PROCESSA SENSORES (/sensors)
        # ---------------------------------------------------------------
        if subtopic == "sensors":
            doc = json.loads(payload_str)
            
            # ESP32 envia "humidity" e "temperature"
            umidade = doc.get("humidity")
            temperatura = doc.get("temperature", 0.0)  # Caso não venha leitura de temp

            if umidade is not None:
                salvar_no_banco(
                    planta_id=device_id,
                    umidade=float(umidade),
                    temperatura=float(temperatura)
                )
            else:
                logging.warning(f"Payload de sensores inválido de ESP {device_id}: {payload_str}")

        # ---------------------------------------------------------------
        # 2. PROCESSA ESTADO DA BOMBA (/pump)
        # ---------------------------------------------------------------
        elif subtopic == "pump":
            doc = json.loads(payload_str)
            active = doc.get("active", False)
            estado_str = "LIGADA 🟢" if active else "DESLIGADA 🔴"
            logging.info(f"[BOMBA] ESP {device_id} -> Bomba está {estado_str}")

        # ---------------------------------------------------------------
        # 3. PROCESSA CONEXÃO / LWT (/status)
        # ---------------------------------------------------------------
        elif subtopic == "status":
            doc = json.loads(payload_str)
            status = doc.get("status", "desconhecido")
            logging.info(f"[STATUS] ESP {device_id} reportou estado: {status.upper()}")

    except json.JSONDecodeError:
        logging.error(f"Erro de parsing JSON no tópico {msg.topic}. Payload: {msg.payload}")
    except Exception as e:
        logging.error(f"Erro inesperado ao processar mensagem do tópico {msg.topic}: {e}")

# -------------------------------------------------------------------
# LOOP PRINCIPAL
# -------------------------------------------------------------------
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info("Iniciando serviço de escuta MQTT no Raspberry Pi...")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        logging.info("Encerrando o serviço MQTT.")
        client.disconnect()
    except Exception as e:
        logging.critical(f"Erro na conexão com Mosquitto: {e}")

if __name__ == "__main__":
    main()