#pragma once

namespace pump_control {

void begin();

// Reavalia se a bomba deve ligar/desligar com base na umidade atual e no
// threshold configurado. Usa histerese para não ficar ligando/desligando
// toda hora perto do limite. Retorna true se o estado da bomba mudou
// (útil para saber quando publicar a atualização via MQTT).
bool update(float currentHumidity, float threshold);

bool isActive();

// Desliga a bomba imediatamente (ex: sensor com falha, comando manual).
void forceOff();

} // namespace pump_control