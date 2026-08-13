from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db import schemas
from crud import devices


router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)


# ============================================================
# CREATE
# ============================================================

@router.post(
    "/",
    response_model=schemas.DeviceResponse
)
def create_device(
    device: schemas.DeviceCreate,
    db: Session = Depends(get_db)
):

    existing = devices.get_device_by_client_id(
        db,
        device.mqtt_client_id
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Device already registered"
        )


    return devices.create_device(
        db,
        device
    )


# ============================================================
# GET ALL
# ============================================================

@router.get(
    "/",
    response_model=List[schemas.DeviceResponse]
)
def read_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):

    return devices.get_devices(
        db,
        skip,
        limit
    )


# ============================================================
# GET ONE
# ============================================================

@router.get(
    "/{device_id}",
    response_model=schemas.DeviceResponse
)
def read_device(
    device_id: str,
    db: Session = Depends(get_db)
):

    device = devices.get_device(
        db,
        device_id
    )


    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )


    return device


# ============================================================
# UPDATE
# ============================================================

@router.patch(
    "/{device_id}",
    response_model=schemas.DeviceResponse
)
def update_device(
    device_id: str,
    device_update: schemas.DeviceUpdate,
    db: Session = Depends(get_db)
):

    device = devices.update_device(
        db,
        device_id,
        device_update
    )


    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )


    return device


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{device_id}",
    response_model=schemas.DeviceResponse
)
def delete_device(
    device_id: str,
    db: Session = Depends(get_db)
):

    device = devices.delete_device(
        db,
        device_id
    )


    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )


    return device