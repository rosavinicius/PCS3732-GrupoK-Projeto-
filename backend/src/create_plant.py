import argparse
import sys

from db.database import SessionLocal
from db.schemas import PlantCreate
from crud.devices import get_device, get_devices
from crud.plants import create_plant, get_plants


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

        print(
            f"- id: {device_id}\n"
            f"  name: {name}\n"
            f"  mqtt_client_id: {mqtt_client_id}\n"
        )


def has_plant_for_device(db, device_id):
    plants = get_plants(db)
    return any(
        getattr(plant, "device_id", None) == device_id
        for plant in plants
    )


def create_plant_record(db, device_id, name, species, min_moisture, max_moisture):
    if not get_device(db, device_id):
        print(f"Erro: dispositivo com id '{device_id}' não existe.")
        return None

    if has_plant_for_device(db, device_id):
        print(f"Erro: já existe uma planta associada ao dispositivo {device_id}.")
        return None

    plant_data = PlantCreate(
        device_id=device_id,
        name=name,
        species=species,
        min_moisture=min_moisture,
        max_moisture=max_moisture,
    )

    created = create_plant(db, plant_data)
    return created


def parse_args():
    parser = argparse.ArgumentParser(
        description="Cadastrar planta no banco de dados do backend."
    )

    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="Listar dispositivos existentes no banco de dados.",
    )

    parser.add_argument(
        "--device-id",
        type=str,
        help="ID do dispositivo já cadastrado no banco.",
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Nome da planta.",
    )

    parser.add_argument(
        "--species",
        type=str,
        default=None,
        help="Espécie da planta (opcional).",
    )

    parser.add_argument(
        "--min-moisture",
        type=float,
        help="Valor mínimo de umidade da planta.",
    )

    parser.add_argument(
        "--max-moisture",
        type=float,
        help="Valor máximo de umidade da planta.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    db = SessionLocal()

    try:
        if args.list_devices:
            list_devices(db)
            return

        required = [args.device_id, args.name, args.min_moisture, args.max_moisture]

        if any(value is None for value in required):
            print(
                "Para criar uma planta, informe --device-id, --name, --min-moisture e --max-moisture."
            )
            print("Use --help para ver todas as opções.")
            sys.exit(1)

        created = create_plant_record(
            db,
            args.device_id,
            args.name,
            args.species,
            args.min_moisture,
            args.max_moisture,
        )

        if created is None:
            sys.exit(1)

        print("Planta criada com sucesso:")
        print(f"- id: {getattr(created, 'id', None)}")
        print(f"- device_id: {getattr(created, 'device_id', None)}")
        print(f"- name: {getattr(created, 'name', None)}")
        print(f"- species: {getattr(created, 'species', None)}")
        print(f"- min_moisture: {getattr(created, 'min_moisture', None)}")
        print(f"- max_moisture: {getattr(created, 'max_moisture', None)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
