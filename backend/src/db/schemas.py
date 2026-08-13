from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ============================================================
# ENUMS
# ============================================================

class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class IrrigationTrigger(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


# ============================================================
# DEVICE
# ============================================================

class DeviceBase(BaseModel):
    mqtt_client_id: str
    name: str
    ip: Optional[str] = None
    firmware: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    firmware: Optional[str] = None
    status: Optional[DeviceStatus] = None


class DeviceResponse(DeviceBase):
    id: str
    status: DeviceStatus
    last_seen: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# PLANT
# ============================================================

class PlantBase(BaseModel):
    name: str
    species: Optional[str] = None
    min_moisture: float
    max_moisture: float


class PlantCreate(PlantBase):
    device_id: str


class PlantUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    min_moisture: Optional[float] = None
    max_moisture: Optional[float] = None


class PlantResponse(PlantBase):
    id: str
    device_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# SENSOR READING
# ============================================================

class SensorReadingCreate(BaseModel):
    plant_id: str
    soil_moisture: float
    temperature: float


class SensorReadingResponse(BaseModel):
    id: str
    plant_id: str
    timestamp: datetime
    soil_moisture: float
    temperature: float

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# IRRIGATION EVENT
# ============================================================

class IrrigationEventCreate(BaseModel):
    plant_id: str
    duration_seconds: float
    water_amount_ml: Optional[float] = None
    trigger: IrrigationTrigger = IrrigationTrigger.AUTOMATIC


class IrrigationEventResponse(BaseModel):
    id: str
    plant_id: str
    start_time: datetime
    duration_seconds: float
    water_amount_ml: Optional[float]
    trigger: IrrigationTrigger

    model_config = ConfigDict(from_attributes=True)