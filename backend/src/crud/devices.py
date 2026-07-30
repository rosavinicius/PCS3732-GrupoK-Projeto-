from sqlalchemy.orm import Session

from db import models
from db import schemas


# ============================================================
# CREATE
# ============================================================

def create_device(
    db: Session,
    device: schemas.DeviceCreate
):
    """
    Cria um novo ESP32 no banco.
    """

    db_device = models.Device(
        mqtt_client_id=device.mqtt_client_id,
        name=device.name,
        ip=device.ip,
        firmware=device.firmware,
    )

    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    return db_device


# ============================================================
# READ
# ============================================================

def get_device(
    db: Session,
    device_id: int
):
    """
    Busca um ESP32 pelo ID.
    """

    return (
        db.query(models.Device)
        .filter(
            models.Device.id == device_id
        )
        .first()
    )


def get_device_by_client_id(
    db: Session,
    mqtt_client_id: str
):
    """
    Busca um ESP32 pelo identificador MQTT.
    
    Exemplo:
    esp32-vaso-01
    """

    return (
        db.query(models.Device)
        .filter(
            models.Device.mqtt_client_id == mqtt_client_id
        )
        .first()
    )


def get_devices(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    """
    Lista todos os ESP32 cadastrados.
    """

    return (
        db.query(models.Device)
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# UPDATE
# ============================================================

def update_device(
    db: Session,
    device_id: int,
    device_update: schemas.DeviceUpdate
):
    """
    Atualiza informações de um ESP32.
    """

    db_device = get_device(
        db,
        device_id
    )

    if not db_device:
        return None


    update_data = device_update.model_dump(
        exclude_unset=True
    )


    for key, value in update_data.items():
        setattr(
            db_device,
            key,
            value
        )


    db.commit()
    db.refresh(db_device)

    return db_device



def update_device_status(
    db: Session,
    mqtt_client_id: str,
    status: schemas.DeviceStatus
):
    """
    Atualiza status e última conexão
    de um ESP32.
    """

    device = get_device_by_client_id(
        db,
        mqtt_client_id
    )

    if not device:
        return None


    device.status = status

    if status == schemas.DeviceStatus.ONLINE:
        from datetime import datetime
        device.last_seen = datetime.now()


    db.commit()
    db.refresh(device)

    return device



# ============================================================
# DELETE
# ============================================================

def delete_device(
    db: Session,
    device_id: int
):
    """
    Remove um ESP32.
    """

    db_device = get_device(
        db,
        device_id
    )

    if not db_device:
        return None


    db.delete(db_device)
    db.commit()

    return db_device