import json
from typing import List
import paho.mqtt.client as mqtt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db.database import get_db
from db import schemas
from crud import plants, devices

router = APIRouter(
    prefix="/plants",
    tags=["Plants"]
)

# ============================================================
# PLANTS CRUD
# ============================================================

@router.post(
    "/",
    response_model=schemas.PlantResponse
)
def create_plant(
    plant: schemas.PlantCreate,
    db: Session = Depends(get_db)
):
    return plants.create_plant(db, plant)


@router.get(
    "/",
    response_model=List[schemas.PlantResponse]
)
def read_plants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return plants.get_plants(db, skip=skip, limit=limit)


@router.get(
    "/{plant_id}",
    response_model=schemas.PlantResponse
)
def read_plant(
    plant_id: str,
    db: Session = Depends(get_db)
):
    plant = plants.get_plant(db, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Planta não encontrada")
    return plant


# Rota específica deve vir ANTES da genérica /{plant_id}
class ThresholdUpdate(BaseModel):
    min_moisture: float


@router.patch("/{plant_id}/threshold")
def update_plant_threshold(plant_id: str, threshold_data: ThresholdUpdate, db: Session = Depends(get_db)):
    """
    Atualiza o limiar de umidade da planta no Banco de Dados 
    e envia a nova configuração para o respectivo ESP32 via MQTT.
    """
    
    # Passo A: Buscar a planta no banco de dados
    plant = plants.get_plant(db, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Planta não encontrada")
    
    # Passo B: Atualizar o limite (min_moisture) da planta usando o CRUD existente
    plant_update = schemas.PlantUpdate(min_moisture=threshold_data.min_moisture)
    plants.update_plant(db, plant_id, plant_update)
    
    # Passo C: Buscar o dispositivo atrelado a essa planta para saber o ID MQTT
    device = devices.get_device(db, plant.device_id)
    if device:
        try:
            # Conecta ao broker MQTT local
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.connect("localhost", 1883)
            
            # O main.py processa o ID do dispositivo no tópico como um inteiro
            topic = f"devices/{device.id}/config"
            
            # Cria o payload em JSON exatamente como o ESP32 espera
            payload = json.dumps({"humidityThreshold": float(threshold_data.min_moisture)})
            
            # Envia com retain=True para que o ESP32 receba mesmo se estiver offline no momento
            client.publish(topic, payload, qos=1, retain=True)
            client.disconnect()
            
        except Exception as e:
            # Se o MQTT falhar (ex: broker offline), a API não quebra, apenas avisa.
            return {
                "message": "Limiar atualizado no banco de dados, mas falha ao notificar o ESP32 (MQTT).",
                "error": str(e)
            }

    return {"message": f"Limiar da planta {plant.name} atualizado com sucesso para {threshold_data.min_moisture}%!"}


@router.patch(
    "/{plant_id}"
)
def update_plant(
    plant_id: str,
    plant_update: schemas.PlantUpdate,
    db: Session = Depends(get_db)
):
    plant = plants.update_plant(db, plant_id, plant_update)
    if not plant:
        raise HTTPException(status_code=404, detail="Planta não encontrada")
    return plant


@router.delete(
    "/{plant_id}",
    response_model=schemas.PlantResponse
)
def delete_plant(
    plant_id: str,
    db: Session = Depends(get_db)
):
    plant = plants.delete_plant(db, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Planta não encontrada")
    return plant