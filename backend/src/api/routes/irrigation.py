from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from db.database import get_db
from db import schemas

from crud import irrigation


router = APIRouter(
    prefix="/irrigation",
    tags=["Irrigation"]
)



# ============================================================
# CREATE
# ============================================================

@router.post(
    "/",
    response_model=schemas.IrrigationEventResponse
)
def create_irrigation(
    event: schemas.IrrigationEventCreate,
    db: Session = Depends(get_db)
):
    """
    Registra uma irrigação realizada.
    """

    return irrigation.create_irrigation_event(
        db,
        event
    )



# ============================================================
# GET HISTORY BY PLANT
# ============================================================

@router.get(
    "/plants/{plant_id}",
    response_model=List[schemas.IrrigationEventResponse]
)
def get_irrigation_history(
    plant_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de irrigação
    de uma planta.
    """

    return irrigation.get_plant_irrigations(
        db,
        plant_id,
        limit
    )



# ============================================================
# GET LAST IRRIGATION
# ============================================================

@router.get(
    "/plants/{plant_id}/last",
    response_model=schemas.IrrigationEventResponse
)
def get_last_irrigation(
    plant_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna a última vez que a planta
    foi irrigada.
    """

    event = irrigation.get_last_irrigation(
        db,
        plant_id
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="No irrigation event found"
        )

    return event



# ============================================================
# WATER STATISTICS
# ============================================================

@router.get(
    "/plants/{plant_id}/water"
)
def get_water_usage(
    plant_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna consumo total estimado de água.
    """

    return {
        "plant_id": plant_id,
        "total_water_ml":
            irrigation.get_total_water_used(
                db,
                plant_id
            )
    }



# ============================================================
# TIME STATISTICS
# ============================================================

@router.get(
    "/plants/{plant_id}/time"
)
def get_irrigation_time(
    plant_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna tempo total de funcionamento
    da bomba.
    """

    return {
        "plant_id": plant_id,
        "total_seconds":
            irrigation.get_total_irrigation_time(
                db,
                plant_id
            )
    }



# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{irrigation_id}",
    response_model=schemas.IrrigationEventResponse
)
def delete_irrigation(
    irrigation_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove um evento de irrigação.
    """

    event = irrigation.delete_irrigation(
        db,
        irrigation_id
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Irrigation event not found"
        )

    return event