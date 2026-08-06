#pragma once

#include <Arduino.h>
#include "sensors.h"

namespace mqtt_client {

// Callback disparado quando chega uma nova config de threshold vinda do
// backend (usuário mexeu no slider no dashboard).
typedef void (*ConfigCallback)(float newThreshold);

void begin(const String& deviceId, ConfigCallback onConfig);

// Chamar no loop() - mantém a conexão viva e processa mensagens recebidas.
void poll();

bool isConnected();

// devices/{id}/sensors -> leitura periódica
void publishSensorReading(const sensors::Reading& reading);

// devices/{id}/pump -> retained, muda só quando o estado da bomba muda
void publishPumpStatus(bool active);

// devices/{id}/status -> retained, {"status":"online","name":deviceId}
// Chamado automaticamente ao (re)conectar. O LWT cuida do "offline"
// automaticamente se a conexão cair sem aviso.
void publishOnlineStatus();

} // namespace mqtt_client