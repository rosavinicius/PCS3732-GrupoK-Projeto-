#pragma once

#include "sensors.h"

namespace display {

void begin();

// Atualiza a tela com a leitura atual, o threshold configurado e o estado da bomba.
// Mantém um pequeno histórico interno de umidade para desenhar a série temporal.
void update(const sensors::Reading& reading, float threshold, bool pumpActive, bool mqttConnected);

} // namespace display