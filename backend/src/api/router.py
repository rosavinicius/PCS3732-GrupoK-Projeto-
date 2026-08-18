from fastapi import APIRouter

from api.routes import (
    plants,
    devices,
    sensors,
    irrigation,
)


api_router = APIRouter()

api_router.include_router(
    plants.router
)

api_router.include_router(
    devices.router
)

api_router.include_router(
    sensors.router
)

api_router.include_router(
    irrigation.router
)