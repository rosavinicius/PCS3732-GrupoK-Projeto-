from fastapi import APIRouter

from api.routes import (
    plants,
    devices,
    readings,
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
    readings.router
)

api_router.include_router(
    irrigation.router
)