#pragma once

// ---------------------------------------------------------------------------
// Wi-Fi
// ---------------------------------------------------------------------------
#define WIFI_SSID       "iPhone de bia"
#define WIFI_PASSWORD   "12345678"
#define WIFI_RETRY_MS   5000

// ---------------------------------------------------------------------------
// MQTT broker (Raspberry Pi rodando Mosquitto)
// ---------------------------------------------------------------------------
#define MQTT_BROKER_HOST   "raspberry-pi-labproc-4.local"
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
#define PIN_SOIL_MOISTURE   0   // ADC - sensor capacitivo de umidade do solo
#define PIN_SOIL_TEMP       3    // OneWire - DS18B20 (sonda de temperatura do solo)
#define PIN_PUMP_RELAY      5   // saída digital - relé que aciona a bomba
#define PIN_STATUS_LED      8    // LED onboard, pisca em atividade

#define LCD_SDA      6
#define LCD_SCL      7
#define LCD_ADDR     0x27

// ---------------------------------------------------------------------------
// Comportamento
// ---------------------------------------------------------------------------
#define SENSOR_READ_INTERVAL_MS   5000   // lê e publica sensores a cada 10s
#define DISPLAY_UPDATE_INTERVAL_MS 5000
#define DEFAULT_HUMIDITY_THRESHOLD 30.0f  // usado só se nada estiver salvo na flash
#define PUMP_HYSTERESIS_PERCENT    3.0f   // evita a bomba ligar/desligar em flapping
#define MAX_PUMP_TIME  60000              // 60 segundos

// Calibração do sensor de umidade capacitivo (ajustar após teste no solo seco/molhado)
#define SOIL_MOISTURE_RAW_DRY   4095
#define SOIL_MOISTURE_RAW_WET   1000

// Pump relay: HIGH = ligado, LOW = desligado (inverso do relé)
#define PUMP_ON_LEVEL  HIGH
#define PUMP_OFF_LEVEL LOW