#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "mqtt_client.h"
#include "sensors.h"
#include "pump_control.h"
#include "storage.h"
#include "display.h"

static float humidityThreshold = DEFAULT_HUMIDITY_THRESHOLD;
static unsigned long lastSensorReadAt = 0;
static unsigned long lastDisplayUpdateAt = 0;
static sensors::Reading lastReading = { NAN, NAN, NAN };

// Chamado pelo mqtt_client quando o usuário muda o threshold no dashboard.
static void onConfigReceived(float newThreshold) {
    humidityThreshold = newThreshold;
    storage::saveHumidityThreshold(newThreshold);
}

void setup() {
    Serial.begin(115200);
    delay(200);

    pinMode(PIN_STATUS_LED, OUTPUT);

    storage::begin();
    humidityThreshold = storage::loadHumidityThreshold();
    Serial.printf("[main] threshold carregado da flash: %.1f%%\n", humidityThreshold);

    sensors::begin();
    pump_control::begin();
    display::begin();

    wifi_manager::begin();

    String deviceId = wifi_manager::getDeviceId();
    Serial.printf("[main] device id: %s\n", deviceId.c_str());
    mqtt_client::begin(deviceId, onConfigReceived);
}

void loop() {
    wifi_manager::poll();
    mqtt_client::poll();

    unsigned long now = millis();

    if (now - lastSensorReadAt >= SENSOR_READ_INTERVAL_MS) {
        lastSensorReadAt = now;

        lastReading = sensors::read();
        Serial.printf("[main] leitura: umidade=%.1f%% temp=%.1fC ph=%.1f\n",
                      lastReading.humidity, lastReading.temperature, lastReading.ph);

        mqtt_client::publishSensorReading(lastReading);

        bool pumpChanged = pump_control::update(lastReading.humidity, humidityThreshold);
        if (pumpChanged) {
            mqtt_client::publishPumpStatus(pump_control::isActive());
        }

        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED)); // pisca a cada leitura
    }

    if (now - lastDisplayUpdateAt >= DISPLAY_UPDATE_INTERVAL_MS) {
        lastDisplayUpdateAt = now;
        display::update(lastReading, humidityThreshold, pump_control::isActive(),
                         mqtt_client::isConnected());
    }
}