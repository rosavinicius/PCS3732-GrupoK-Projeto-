import argparse
import sys

from db.database import SessionLocal
from db.schemas import DeviceCreate
from crud.devices import create_device, get_device_by_client_id, get_devices


def list_devices(db):
    devices = get_devices(db)

    if not devices:
        print("Nenhum dispositivo encontrado no banco de dados.")
        return

    print("Dispositivos cadastrados:")
    for device in devices:
        device_id = getattr(device, "id", None)
        name = getattr(device, "name", None)
        mqtt_client_id = getattr(device, "mqtt_client_id", None)
        status = getattr(device, "status", None)
        print(
            f"- id: {device_id}\n"
            f"  name: {name}\n"
            f"  mqtt_client_id: {mqtt_client_id}\n"
            f"  status: {status}\n"
        )


def create_device_record(db, mqtt_client_id, name, ip, firmware):
    existing = get_device_by_client_id(db, mqtt_client_id)

    if existing:
        print(
            f"Erro: já existe um dispositivo com mqtt_client_id '{mqtt_client_id}'."
        )
        return None

    device_data = DeviceCreate(
        mqtt_client_id=mqtt_client_id,
        name=name,
        ip=ip,
        firmware=firmware,
    )

    created = create_device(db, device_data)
    return created


def parse_args():
    parser = argparse.ArgumentParser(
        description="Cadastrar um dispositivo (device) no banco de dados do backend."
    )

    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Listar dispositivos existentes no banco de dados.",
    )

    parser.add_argument(
        "--mqtt-client-id",
        type=str,
        help="Identificador MQTT do dispositivo (ex: esp32-vaso-01).",
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Nome do dispositivo.",
    )

    parser.add_argument(
        "--ip",
        type=str,
        default=None,
        help="Endereço IP do dispositivo (opcional).",
    )

    parser.add_argument(
        "--firmware",
        type=str,
        default=None,
        help="Versão de firmware do dispositivo (opcional).",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    db = SessionLocal()

    try:
        if args.list_devices:
            list_devices(db)
            return

        if not args.mqtt_client_id or not args.name:
            print(
                "Para criar um device, informe --mqtt-client-id e --name."
            )
            print("Use --help para ver todas as opções.")
            sys.exit(1)

        created = create_device_record(
            db,
            args.mqtt_client_id,
            args.name,
            args.ip,
            args.firmware,
        )

        if created is None:
            sys.exit(1)

        print("Device criado com sucesso:")
        print(f"- id: {getattr(created, 'id', None)}")
        print(f"- mqtt_client_id: {getattr(created, 'mqtt_client_id', None)}")
        print(f"- name: {getattr(created, 'name', None)}")
        print(f"- ip: {getattr(created, 'ip', None)}")
        print(f"- firmware: {getattr(created, 'firmware', None)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
