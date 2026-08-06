#pragma once

#include <Arduino.h>

namespace wifi_manager {

// Conecta (bloqueante) na rede definida em config.h.
void begin();

// Chamar no loop() - reconecta automaticamente se a conexão cair.
void poll();

bool isConnected();

// ID único do dispositivo, derivado do MAC address (ex: "esp32-a1b2c3").
// Usado como MQTT client id e como prefixo de tópico (devices/{id}/...).
String getDeviceId();

} // namespace wifi_manager