#pragma once

namespace sensors {

struct Reading {
    float humidity;     // % (0-100), sensor capacitivo de umidade do solo
    float temperature;  // °C, sonda DS18B20
    float ph;           // 0-14, sensor analógico de PH
};

void begin();

// Faz a leitura de todos os sensores. Bloqueante por alguns ms (conversão do DS18B20).
Reading read();

} // namespace sensors