#include "sensors.h"
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "config.h"

namespace sensors {

static OneWire oneWire(PIN_SOIL_TEMP);
static DallasTemperature tempSensor(&oneWire);

void begin() {
    analogReadResolution(12); // ESP32: 0-4095
    tempSensor.begin();
}

static float readSoilMoisturePercent() {
    int raw = analogRead(PIN_SOIL_MOISTURE);

    // sensor capacitivo: valor RAW alto = seco, valor RAW baixo = molhado
    float pct = map(raw, SOIL_MOISTURE_RAW_DRY, SOIL_MOISTURE_RAW_WET, 0, 100);
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

static float readSoilPh() {
    int raw = analogRead(PIN_SOIL_PH);
    float voltage = (raw / 4095.0f) * 3.3f;
    float ph = PH_SLOPE * (voltage - PH_VOLTAGE_AT_PH7) + 7.0f;
    return constrain(ph, 0.0f, 14.0f);
}

Reading read() {
    Reading r;
    r.humidity = readSoilMoisturePercent();
    r.temperature = readSoilTemperatureCelsius();
    r.ph = readSoilPh();
    return r;
}

} // namespace sensors