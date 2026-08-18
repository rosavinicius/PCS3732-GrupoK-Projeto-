"""
Script para corrigir leituras de sensores que foram salvas
com mqtt_client_id ao invés do plant_id correto.

Uso:
    python backend/src/fix_sensor_readings.py
"""

from db.database import SessionLocal
from crud.plants import get_plants
from crud.devices import get_device
from crud.sensors import update_readings_plant_id


def fix_all_readings():
    """
    Percorre todas as plantas e corrige as leituras
    associadas aos seus dispositivos.
    """
    db = SessionLocal()
    try:
        plants = get_plants(db)
        
        if not plants:
            print("Nenhuma planta encontrada no banco de dados.")
            return
        
        total_updated = 0
        
        for plant in plants:
            device = get_device(db, plant.device_id)
            
            if not device or not device.mqtt_client_id:
                continue
            
            # Tenta atualizar leituras que tenham mqtt_client_id como plant_id
            updated = update_readings_plant_id(
                db=db,
                old_plant_id=device.mqtt_client_id,
                new_plant_id=plant.id
            )
            
            if updated > 0:
                print(
                    f"Planta '{plant.name}' (id={plant.id}): "
                    f"{updated} leituras corrigidas (mqtt_client_id={device.mqtt_client_id})"
                )
                total_updated += updated
        
        if total_updated == 0:
            print("Nenhuma leitura precisou ser corrigida.")
        else:
            print(f"\nTotal de leituras corrigidas: {total_updated}")
            
    except Exception as exc:
        db.rollback()
        print(f"Erro ao corrigir leituras: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Iniciando correção de leituras de sensores...")
    fix_all_readings()
    print("Correção concluída.")
