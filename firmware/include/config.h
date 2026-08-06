#pragma once

// ---------------------------------------------------------------------------
// Wi-Fi
// ---------------------------------------------------------------------------
#define WIFI_SSID       "SUA_REDE_WIFI"
#define WIFI_PASSWORD   "SUA_SENHA_WIFI"
#define WIFI_RETRY_MS   5000

// ---------------------------------------------------------------------------
// MQTT broker (Raspberry Pi rodando Mosquitto)
// ---------------------------------------------------------------------------
#define MQTT_BROKER_HOST   "raspberrypi.local"
#define MQTT_BROKER_PORT   1883
#define MQTT_RECONNECT_MS  3000

// ---------------------------------------------------------------------------
// Identidade do dispositivo
// ---------------------------------------------------------------------------
// O ID é derivado do MAC address do ESP32 em tempo de execução (ver
// wifi_manager.h -> getDeviceId()), então não precisa editar nada aqui.
// Ele é usado tanto como MQTT client id quanto como prefixo de tópico:
//
//   devices/{id}/status    -> retained, online/offline (com LWT)
//   devices/{id}/sensors   -> leituras periódicas (umidade, temp, ph)
//   devices/{id}/config    -> retained, {"humidityThreshold": <0-100>}
//   devices/{id}/pump      -> retained, {"active": bool}
//
#define TOPIC_PREFIX "devices/"

// ---------------------------------------------------------------------------
// Pinos
// ---------------------------------------------------------------------------
#define PIN_SOIL_MOISTURE   34   // ADC - sensor capacitivo de umidade do solo
#define PIN_SOIL_PH         35   // ADC - sensor analógico de PH
#define PIN_SOIL_TEMP       4    // OneWire - DS18B20 (sonda de temperatura do solo)
#define PIN_PUMP_RELAY      26   // saída digital - relé que aciona a bomba
#define PIN_STATUS_LED      2    // LED onboard, pisca em atividade

// OLED via I2C (SDA/SCL default do ESP32: 21/22)
#define OLED_WIDTH   128
#define OLED_HEIGHT  64
#define OLED_ADDR    0x3C

// ---------------------------------------------------------------------------
// Comportamento
// ---------------------------------------------------------------------------
#define SENSOR_READ_INTERVAL_MS   30000   // lê e publica sensores a cada 30s
#define DISPLAY_UPDATE_INTERVAL_MS 1000
#define DEFAULT_HUMIDITY_THRESHOLD 30.0f  // usado só se nada estiver salvo na flash
#define PUMP_HYSTERESIS_PERCENT    3.0f   // evita a bomba ligar/desligar em flapping

// Calibração do sensor de umidade capacitivo (ajustar após teste no solo seco/molhado)
#define SOIL_MOISTURE_RAW_DRY   3000
#define SOIL_MOISTURE_RAW_WET   1200

// Calibração do sensor de PH (ajustar com soluções buffer 4.0 / 7.0)
#define PH_VOLTAGE_AT_PH7  1.65f
#define PH_SLOPE           -5.7f