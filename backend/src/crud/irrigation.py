from sqlalchemy.orm import Session

from db import models
from db import schemas


# ============================================================
# CREATE
# ============================================================

def create_irrigation_event(
    db: Session,
    irrigation: schemas.IrrigationEventCreate
):
    """
    Registra um evento de irrigação.

    Chamado quando uma bomba é acionada.
    """

    db_event = models.IrrigationEvent(
        plant_id=irrigation.plant_id,
        duration_seconds=irrigation.duration_seconds,
        water_amount_ml=irrigation.water_amount_ml,
        trigger=irrigation.trigger,
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event



# ============================================================
# READ
# ============================================================

def get_irrigation(
    db: Session,
    irrigation_id: str
):
    """
    Busca uma irrigação pelo ID.
    """

    return (
        db.query(models.IrrigationEvent)
        .filter(
            models.IrrigationEvent.id == irrigation_id
        )
        .first()
    )



def get_plant_irrigations(
    db: Session,
    plant_id: str,
    limit: int = 100
):
    """
    Retorna o histórico de irrigações
    de uma planta.
    """

    return (
        db.query(models.IrrigationEvent)
        .filter(
            models.IrrigationEvent.plant_id == plant_id
        )
        .order_by(
            models.IrrigationEvent.start_time.desc()
        )
        .limit(limit)
        .all()
    )



def get_last_irrigation(
    db: Session,
    plant_id: str
):
    """
    Retorna a última irrigação
    realizada em uma planta.
    """

    return (
        db.query(models.IrrigationEvent)
        .filter(
            models.IrrigationEvent.plant_id == plant_id
        )
        .order_by(
            models.IrrigationEvent.start_time.desc()
        )
        .first()
    )



# ============================================================
# STATISTICS
# ============================================================

def get_total_water_used(
    db: Session,
    plant_id: str
):
    """
    Retorna a quantidade total estimada
    de água utilizada por uma planta.
    """

    irrigations = (
        db.query(models.IrrigationEvent)
        .filter(
            models.IrrigationEvent.plant_id == plant_id
        )
        .all()
    )

    total = 0

    for irrigation in irrigations:
        if irrigation.water_amount_ml:
            total += irrigation.water_amount_ml

    return total



def get_total_irrigation_time(
    db: Session,
    plant_id: str
):
    """
    Retorna o tempo total que a bomba
    ficou ligada.
    """

    irrigations = (
        db.query(models.IrrigationEvent)
        .filter(
            models.IrrigationEvent.plant_id == plant_id
        )
        .all()
    )

    return sum(
        irrigation.duration_seconds
        for irrigation in irrigations
    )



# ============================================================
# DELETE
# ============================================================

def delete_irrigation(
    db: Session,
    irrigation_id: str
):
    """
    Remove um evento de irrigação.
    """

    event = get_irrigation(
        db,
        irrigation_id
    )

    if not event:
        return None

    db.delete(event)
    db.commit()

    return event