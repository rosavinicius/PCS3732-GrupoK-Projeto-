#pragma once

#include <Arduino.h>
#include "sensors.h"


namespace display {

void begin();


void update(
    const String& plantId,
    const sensors::Reading& reading,
    float threshold,
    bool pumpActive,
    bool mqttConnected
);


}