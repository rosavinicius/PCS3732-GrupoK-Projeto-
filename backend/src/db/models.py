import uuid
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


# ============================================================
# ENUMS
# ============================================================

class IrrigationTrigger(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


# ============================================================
# DEVICE
# ============================================================

class Device(Base):
    __tablename__ = "devices"

    id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    mqtt_client_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    ip = Column(String)
    firmware = Column(String)

    status = Column(
        SqlEnum(DeviceStatus),
        nullable=False,
        default=DeviceStatus.OFFLINE,
    )

    last_seen = Column(DateTime)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Um ESP32 controla exatamente uma planta
    plant = relationship(
        "Plant",
        back_populates="device",
        uselist=False,
    )


# ============================================================
# PLANT
# ============================================================

class Plant(Base):
    __tablename__ = "plants"

    id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    device_id = Column(
        String,
        ForeignKey("devices.id"),
        unique=True,
        nullable=False,
    )

    name = Column(String, nullable=False)

    species = Column(String)

    min_moisture = Column(Float, nullable=False)

    max_moisture = Column(Float, nullable=False)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    device = relationship(
        "Device",
        back_populates="plant",
    )

    sensor_readings = relationship(
        "SensorReading",
        back_populates="plant",
        cascade="all, delete-orphan",
    )

    irrigations = relationship(
        "IrrigationEvent",
        back_populates="plant",
        cascade="all, delete-orphan",
    )


# ============================================================
# SENSOR READING
# ============================================================

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    plant_id = Column(
        String,
        ForeignKey("plants.id"),
        nullable=False,
    )

    timestamp = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    soil_moisture = Column(Float, nullable=False)

    temperature = Column(Float, nullable=False)

    plant = relationship(
        "Plant",
        back_populates="sensor_readings",
    )


# ============================================================
# IRRIGATION EVENT
# ============================================================

class IrrigationEvent(Base):
    __tablename__ = "irrigation_events"

    id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    plant_id = Column(
        String,
        ForeignKey("plants.id"),
        nullable=False,
    )

    start_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    duration_seconds = Column(
        Float,
        nullable=False,
    )

    water_amount_ml = Column(Float)

    trigger = Column(
        SqlEnum(IrrigationTrigger),
        nullable=False,
        default=IrrigationTrigger.AUTOMATIC,
    )

    plant = relationship(
        "Plant",
        back_populates="irrigations",
    )