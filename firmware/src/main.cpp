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


// Inicialização correta da struct
static sensors::Reading lastReading = {
    NAN,  // humidity
    NAN,  // temperature
    0     // timestamp
};


static String deviceId;


// Chamado pelo mqtt_client quando o Raspberry envia nova configuração
static void onConfigReceived(float newThreshold) {

    humidityThreshold = newThreshold;

    storage::saveHumidityThreshold(newThreshold);

    Serial.printf(
        "[main] novo threshold salvo: %.1f%%\n",
        newThreshold
    );
}



void setup() {

    Serial.begin(115200);
    delay(200);


    pinMode(PIN_STATUS_LED, OUTPUT);


    // Inicializa armazenamento local do ESP32
    storage::begin();

    humidityThreshold =
        storage::loadHumidityThreshold();

    Serial.printf(
        "[main] threshold carregado da flash: %.1f%%\n",
        humidityThreshold
    );


    // Inicializa módulos
    sensors::begin();

    pump_control::begin();

    display::begin();


    // WiFi
    wifi_manager::begin();


    // ID único baseado no MAC do ESP32
    deviceId =
        wifi_manager::getDeviceId();


    Serial.printf(
        "[main] device id: %s\n",
        deviceId.c_str()
    );


    // MQTT
    mqtt_client::begin(
        deviceId,
        onConfigReceived
    );
}



void loop() {

    wifi_manager::poll();

    mqtt_client::poll();


    unsigned long now = millis();



    /*
     * Leitura dos sensores
     */
    if (now - lastSensorReadAt >= SENSOR_READ_INTERVAL_MS) {

        lastSensorReadAt = now;


        lastReading =
            sensors::read();


        Serial.printf(
            "[main] leitura: umidade=%.1f%% temp=%.1fC timestamp=%lu\n",
            lastReading.humidity,
            lastReading.temperature,
            lastReading.timestamp
        );



        // Envia dados para Raspberry via MQTT
        mqtt_client::publishSensorReading(
            lastReading
        );



        /*
         * Controle local da bomba
         */
        bool pumpChanged =
            pump_control::update(
                lastReading.humidity,
                humidityThreshold
            );


        if (pumpChanged) {

            mqtt_client::publishPumpStatus(
                pump_control::isActive()
            );
        }



        // LED indica atividade
        digitalWrite(
            PIN_STATUS_LED,
            !digitalRead(PIN_STATUS_LED)
        );
    }



    /*
     * Atualização do display OLED
     */
    if (now - lastDisplayUpdateAt >= DISPLAY_UPDATE_INTERVAL_MS) {

        lastDisplayUpdateAt = now;


        display::update(
            deviceId,
            lastReading,
            humidityThreshold,
            pump_control::isActive(),
            mqtt_client::isConnected()
        );
    }
}