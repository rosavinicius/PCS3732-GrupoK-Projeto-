import json
import logging

import paho.mqtt.client as mqtt

from backend.src.crud.devices import create_device, get_device_by_client_id, update_device_status
from backend.src.crud.sensors import create_sensor_reading
from backend.src.db.database import SessionLocal
from backend.src.db.schemas import DeviceCreate, DeviceStatus, SensorReadingCreate

# Para rodar localmente, instale as dependências e execute:
# pip install paho-mqtt
# python backend/src/mqtt/receiver.py

# -------------------------------------------------------------------
# CONFIGURAÇÕES MQTT
# -------------------------------------------------------------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_SUBSCRIBE_ALL = "devices/+/+"

# -------------------------------------------------------------------
# LOG
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger("mqtt.receiver")


def _parse_device_id(device_id_str: str):
    device_id_str = device_id_str.strip()
    if not device_id_str:
        logger.warning("ID do dispositivo vazio no tópico MQTT")
        return None
    return device_id_str


def _save_sensor_payload(mqtt_client_id: str, payload_str: str):
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error(f"JSON inválido em sensors para dispositivo {mqtt_client_id}: {payload_str}")
        return

    humidity = data.get("humidity")
    temperature = data.get("temperature", 0.0)

    if humidity is None:
        logger.warning(f"Payload de sensors sem humidity para dispositivo {mqtt_client_id}: {payload_str}")
        return

    db = SessionLocal()
    try:
        device = get_device_by_client_id(db, mqtt_client_id)
        if not device:
            logger.info(f"Dispositivo MQTT não cadastrado no banco, criando: {mqtt_client_id}")
            device_payload = DeviceCreate(
                mqtt_client_id=mqtt_client_id,
                name=f"Device {mqtt_client_id}",
                ip=None,
                firmware=None,
            )
            device = create_device(db, device_payload)
            logger.info(f"Device criado automaticamente: id={device.id} mqtt_client_id={device.mqtt_client_id}")

        if not device.plant:
            logger.warning(f"Dispositivo sem planta associada: {mqtt_client_id}")
            return

        humidity_value = float(humidity)
        temperature_value = float(temperature)

        reading = SensorReadingCreate(
            plant_id=device.plant.id,
            soil_moisture=humidity_value,
            temperature=temperature_value,
        )
        saved = create_sensor_reading(db=db, reading=reading)
        logger.info(
            f"[DB] Leitura salva: mqtt_client_id={mqtt_client_id} plant_id={saved.plant_id} "
            f"humidity={saved.soil_moisture} temperature={saved.temperature}"
        )
    except (TypeError, ValueError) as exc:
        logger.error(
            f"Valores de sensor inválidos para dispositivo {mqtt_client_id}: humidity={humidity}, temperature={temperature}"
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"Erro ao gravar leitura no banco para dispositivo {mqtt_client_id}: {exc}")
    finally:
        db.close()


def _save_device_status(mqtt_client_id: str, payload_str: str):
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error(f"JSON inválido em status para dispositivo {mqtt_client_id}: {payload_str}")
        return

    status_value = data.get("status")
    if status_value not in (DeviceStatus.ONLINE, DeviceStatus.OFFLINE):
        logger.warning(f"Status MQTT desconhecido para dispositivo {mqtt_client_id}: {status_value}")
        return

    db = SessionLocal()
    try:
        updated = update_device_status(
            db=db,
            mqtt_client_id=mqtt_client_id,
            status=DeviceStatus(status_value),
        )
        if updated:
            logger.info(f"[DB] Status do dispositivo atualizado: {mqtt_client_id} -> {status_value}")
        else:
            logger.warning(f"Dispositivo não encontrado no banco para status MQTT: {mqtt_client_id}")
    except Exception as exc:
        db.rollback()
        logger.error(f"Erro ao atualizar status de dispositivo {mqtt_client_id}: {exc}")
    finally:
        db.close()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Conectado ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(TOPIC_SUBSCRIBE_ALL)
        logger.info(f"Inscrito no tópico {TOPIC_SUBSCRIBE_ALL}")
    else:
        logger.error(f"Falha ao conectar no broker MQTT (rc={rc})")


def on_message(client, userdata, msg):
    topic_parts = msg.topic.split("/")
    if len(topic_parts) != 3 or topic_parts[0] != "devices":
        return

    device_id = _parse_device_id(topic_parts[1])
    if device_id is None:
        return

    subtopic = topic_parts[2]
    payload_str = msg.payload.decode("utf-8")

    if subtopic == "sensors":
        _save_sensor_payload(device_id, payload_str)
    elif subtopic == "status":
        _save_device_status(device_id, payload_str)
    elif subtopic == "pump":
        logger.info(f"Recebido status de pump para dispositivo {device_id}: {payload_str}")
    else:
        logger.info(f"Tópico MQTT não tratado: {msg.topic}")


def run():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Iniciando receptor MQTT para gravação no banco...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário. Desconectando MQTT.")
        client.disconnect()
    except Exception as exc:
        logger.critical(f"Erro na conexão MQTT: {exc}")


if __name__ == "__main__":
    run()
