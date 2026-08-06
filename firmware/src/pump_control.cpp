#include "pump_control.h"
#include <Arduino.h>
#include "config.h"

namespace pump_control {

static bool active = false;
// instante em que a bomba foi ligada
static unsigned long pumpStartTime = 0;

void begin() {
    pinMode(PIN_PUMP_RELAY, OUTPUT);
    digitalWrite(PIN_PUMP_RELAY, LOW);
    active = false;
    pumpStartTime = 0;
}

bool update(float currentHumidity, float threshold) {

    if (isnan(currentHumidity)) {
        // Sensor com problema: por segurança desliga a bomba
        forceOff();
        return false;
    }

    bool shouldBeActive = active;

    if (!active && currentHumidity < threshold) {
        shouldBeActive = true;
    }
    else if (active &&
             currentHumidity > threshold + PUMP_HYSTERESIS_PERCENT) {
        shouldBeActive = false;
    }

    if (shouldBeActive != active) {

        active = shouldBeActive;

        digitalWrite(PIN_PUMP_RELAY, active ? HIGH : LOW);

        if (active) {
            pumpStartTime = millis();
        }
        else {
            pumpStartTime = 0;
        }

        Serial.printf(
            "[pump] %s (umidade=%.1f%%, threshold=%.1f%%)\n",
            active ? "LIGOU" : "DESLIGOU",
            currentHumidity,
            threshold
        );
        return true;
    }

    return false;
}

void loop() {

    if (!active)
        return;

    unsigned long elapsed = millis() - pumpStartTime;

    if (elapsed >= MAX_PUMP_TIME) {

        Serial.println("[pump] Tempo máximo excedido.");

        forceOff();
    }
}

bool isActive() {
    return active;
}

void forceOff() {

    if (!active)
        return;

    active = false;
    pumpStartTime = 0;

    digitalWrite(PIN_PUMP_RELAY, LOW);
    Serial.println("[pump] desligada (forceOff)");
}

}