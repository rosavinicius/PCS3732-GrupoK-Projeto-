from datetime import datetime

from sqlalchemy.orm import Session

from db import models
from db import schemas


# ============================================================
# CREATE
# ============================================================

def create_sensor_reading(
    db: Session,
    reading: schemas.SensorReadingCreate
):
    """
    Salva uma nova leitura de umidade.
    
    Normalmente será chamada pelo MQTT handler
    quando um ESP32 enviar dados.
    """

    db_reading = models.SensorReading(
        plant_id=reading.plant_id,
        soil_moisture=reading.soil_moisture,
        temperature=reading.temperature,
    )

    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)

    return db_reading



# ============================================================
# READ
# ============================================================

def get_reading(
    db: Session,
    reading_id: str
):
    """
    Busca uma leitura específica.
    """

    return (
        db.query(models.SensorReading)
        .filter(
            models.SensorReading.id == reading_id
        )
        .first()
    )



def get_plant_history(
    db: Session,
    plant_id: str,
    limit: int = 500
):
    """
    Retorna o histórico de umidade de uma planta.

    Ordenado da leitura mais recente para a mais antiga.
    """

    return (
        db.query(models.SensorReading)
        .filter(
            models.SensorReading.plant_id == plant_id
        )
        .order_by(
            models.SensorReading.timestamp.desc()
        )
        .limit(limit)
        .all()
    )



def get_latest_reading(
    db: Session,
    plant_id: str
):
    """
    Retorna a última leitura recebida
    de uma planta.
    """

    return (
        db.query(models.SensorReading)
        .filter(
            models.SensorReading.plant_id == plant_id
        )
        .order_by(
            models.SensorReading.timestamp.desc()
        )
        .first()
    )



def get_history_between_dates(
    db: Session,
    plant_id: str,
    start: datetime,
    end: datetime
):
    """
    Retorna leituras dentro de um intervalo de tempo.
    """

    return (
        db.query(models.SensorReading)
        .filter(
            models.SensorReading.plant_id == plant_id,
            models.SensorReading.timestamp >= start,
            models.SensorReading.timestamp <= end,
        )
        .order_by(
            models.SensorReading.timestamp
        )
        .all()
    )



# ============================================================
# DELETE
# ============================================================

def delete_reading(
    db: Session,
    reading_id: str
):
    """
    Remove uma leitura.
    """

    reading = get_reading(
        db,
        reading_id
    )

    if not reading:
        return None


    db.delete(reading)
    db.commit()

    return reading


# ============================================================
# UPDATE
# ============================================================

def update_readings_plant_id(
    db: Session,
    old_plant_id: str,
    new_plant_id: str
):
    """
    Atualiza o plant_id de leituras antigas.
    
    Útil quando uma planta é associada a um dispositivo
    que já tinha leituras salvas com mqtt_client_id incorreto.
    """

    updated_count = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.plant_id == old_plant_id)
        .update({"plant_id": new_plant_id})
    )

    db.commit()

    return updated_count