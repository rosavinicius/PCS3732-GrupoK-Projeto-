import json
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

# 1. Definimos um schema apenas para a requisição de Threshold
class ThresholdUpdate(BaseModel):
    min_moisture: float

# 2. Criamos a rota PATCH definitiva
@router.patch("/{plant_id}/threshold")
def update_plant_threshold(plant_id: int, threshold_data: ThresholdUpdate, db: Session = Depends(get_db)):
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