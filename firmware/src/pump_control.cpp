#include "pump_control.h"
#include <Arduino.h>
#include "config.h"

namespace pump_control {

static bool active = false;

void begin() {
    pinMode(PIN_PUMP_RELAY, OUTPUT);
    digitalWrite(PIN_PUMP_RELAY, LOW);
    active = false;
}

bool update(float currentHumidity, float threshold) {
    if (isnan(currentHumidity)) {
        // sensor com problema: por segurança, não liga a bomba às cegas
        forceOff();
        return false;
    }

    bool shouldBeActive = active;

    if (!active && currentHumidity < threshold) {
        shouldBeActive = true;
    } else if (active && currentHumidity > threshold + PUMP_HYSTERESIS_PERCENT) {
        // só desliga quando passar do threshold + margem, evitando flapping
        shouldBeActive = false;
    }

    if (shouldBeActive != active) {
        active = shouldBeActive;
        digitalWrite(PIN_PUMP_RELAY, active ? HIGH : LOW);
        Serial.printf("[pump] %s (umidade=%.1f%%, threshold=%.1f%%)\n",
                      active ? "LIGOU" : "DESLIGOU", currentHumidity, threshold);
        return true;
    }

    return false;
}

bool isActive() {
    return active;
}

void forceOff() {
    if (active) {
        active = false;
        digitalWrite(PIN_PUMP_RELAY, LOW);
        Serial.println("[pump] desligada (forceOff)");
    }
}

} // namespace pump_control