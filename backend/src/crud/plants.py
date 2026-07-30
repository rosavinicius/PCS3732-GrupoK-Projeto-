from sqlalchemy.orm import Session

from db import models
from db import schemas


# ============================================================
# CREATE
# ============================================================

def create_plant(
    db: Session,
    plant: schemas.PlantCreate
):
    """
    Cria uma nova planta no banco.
    """

    db_plant = models.Plant(
        device_id=plant.device_id,
        name=plant.name,
        species=plant.species,
        min_moisture=plant.min_moisture,
        max_moisture=plant.max_moisture,
    )

    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)

    return db_plant


# ============================================================
# READ
# ============================================================

def get_plant(
    db: Session,
    plant_id: int
):
    """
    Retorna uma planta pelo ID.
    """

    return (
        db.query(models.Plant)
        .filter(
            models.Plant.id == plant_id
        )
        .first()
    )


def get_plants(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    """
    Retorna todas as plantas.
    """

    return (
        db.query(models.Plant)
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============================================================
# UPDATE
# ============================================================

def update_plant(
    db: Session,
    plant_id: int,
    plant_update: schemas.PlantUpdate
):
    """
    Atualiza uma planta existente.
    """

    db_plant = get_plant(
        db,
        plant_id
    )

    if not db_plant:
        return None


    update_data = plant_update.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(
            db_plant,
            key,
            value
        )


    db.commit()
    db.refresh(db_plant)

    return db_plant


# ============================================================
# DELETE
# ============================================================

def delete_plant(
    db: Session,
    plant_id: int
):
    """
    Remove uma planta.
    """

    db_plant = get_plant(
        db,
        plant_id
    )

    if not db_plant:
        return None


    db.delete(db_plant)
    db.commit()

    return db_plant