from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from db.database import get_db
from db import schemas
from crud import sensors


router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"]
)



# ============================================================
# CREATE READING
# ============================================================

@router.post(
    "/readings",
    response_model=schemas.SensorReadingResponse
)
def create_reading(
    reading: schemas.SensorReadingCreate,
    db: Session = Depends(get_db)
):
    """
    Insere uma nova leitura.

    Normalmente será usado pelo MQTT,
    mas é útil para testes.
    """

    return sensors.create_sensor_reading(
        db,
        reading
    )



# ============================================================
# GET HISTORY
# ============================================================

@router.get(
    "/plants/{plant_id}/history",
    response_model=List[schemas.SensorReadingResponse]
)
def get_history(
    plant_id: str,
    limit: int = Query(
        default=500,
        le=5000
    ),
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de umidade
    de uma planta.
    """

    return sensors.get_plant_history(
        db,
        plant_id,
        limit
    )



# ============================================================
# GET LATEST
# ============================================================

@router.get(
    "/plants/{plant_id}/latest",
    response_model=schemas.SensorReadingResponse
)
def get_latest(
    plant_id: str,
    db: Session = Depends(get_db)
):

    reading = sensors.get_latest_reading(
        db,
        plant_id
    )


    if not reading:
        raise HTTPException(
            status_code=404,
            detail="No sensor data found"
        )


    return reading



# ============================================================
# GET BETWEEN DATES
# ============================================================

@router.get(
    "/plants/{plant_id}/history/range",
    response_model=List[schemas.SensorReadingResponse]
)
def get_history_range(
    plant_id: str,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db)
):

    return sensors.get_history_between_dates(
        db,
        plant_id,
        start,
        end
    )