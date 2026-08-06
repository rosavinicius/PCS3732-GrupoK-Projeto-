#pragma once

#include <Arduino.h>

namespace sensors {

struct Reading {

    float humidity;     
    float temperature;  

    uint32_t timestamp; // millis() desde o boot do ESP32
};


void begin();

Reading read();


} // namespace sensors