#include "sensors.h"
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "config.h"
#include <stdint.h>

namespace sensors {

static OneWire oneWire(PIN_SOIL_TEMP);
static DallasTemperature tempSensor(&oneWire);

void begin() {
    analogReadResolution(12); // ESP32: 0-4095
    tempSensor.begin();

    Serial.printf(
        "[sensors] sensores OneWire encontrados: %d\n",
        tempSensor.getDeviceCount()
    );
}

static float readSoilMoisturePercent() {
    int raw = analogRead(PIN_SOIL_MOISTURE);
    Serial.print("Soil RAW: ");
    Serial.println(raw);

    float rawDry = SOIL_MOISTURE_RAW_DRY;
    float rawWet = SOIL_MOISTURE_RAW_WET;
    float pct = 100.0f * (raw - rawDry) / (rawWet - rawDry);
    return constrain(pct, 0.0f, 100.0f);
}

static float readSoilTemperatureCelsius() {
    tempSensor.requestTemperatures();
    float t = tempSensor.getTempCByIndex(0);

    // DEVICE_DISCONNECTED_C indica sonda desconectada/com falha
    if (t == DEVICE_DISCONNECTED_C) {
        Serial.println("[sensors] sonda de temperatura desconectada");
        return NAN;
    }
    return t;
}


Reading read() {
    Reading r;
    r.humidity = readSoilMoisturePercent();
    r.temperature = readSoilTemperatureCelsius();
    r.timestamp = millis();
    return r;
}

} // namespace sensors