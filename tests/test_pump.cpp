// Para rodar localmente: pio test -e esp32dev na pasta firmware/ (onde o platformio.ini está)

#include <Arduino.h>
#include <unity.h>
#include "pump_control.h"

// Função executada antes de cada teste
void setUp(void) {
    pump_control::begin();
    pump_control::forceOff();
}

// Função executada depois de cada teste
void tearDown(void) {
    pump_control::forceOff();
}

void test_pump_turns_on_below_threshold(void) {
    float threshold = 40.0f;
    float currentHumidity = 30.0f; // Solo muito seco
    
    bool changed = pump_control::update(currentHumidity, threshold);
    
    TEST_ASSERT_TRUE(changed); // Estado deve ter mudado
    TEST_ASSERT_TRUE(pump_control::isActive()); // Bomba deve estar ligada
}

void test_pump_hysteresis_logic(void) {
    float threshold = 40.0f;
    // O config.h define PUMP_HYSTERESIS_PERCENT como 3.0f, então desliga em 43.0f
    
    // 1. Liga a bomba
    pump_control::update(39.0f, threshold);
    TEST_ASSERT_TRUE(pump_control::isActive());
    
    // 2. Umidade sobe para 41 (Acima do threshold, mas dentro da histerese)
    bool changed = pump_control::update(41.0f, threshold);
    TEST_ASSERT_FALSE(changed); // Não deve mudar
    TEST_ASSERT_TRUE(pump_control::isActive()); // Continua ligada
    
    // 3. Umidade atinge threshold + histerese (40 + 3.0 = 43.0)
    changed = pump_control::update(44.0f, threshold);
    TEST_ASSERT_TRUE(changed); // Estado mudou
    TEST_ASSERT_FALSE(pump_control::isActive()); // Bomba desligou
}

void test_sensor_error_forces_pump_off(void) {
    pump_control::update(30.0f, 40.0f); // Liga
    
    // Simula leitura NAN (falha do sensor reportada em pump_control.cpp)
    bool changed = pump_control::update(NAN, 40.0f);
    
    TEST_ASSERT_FALSE(pump_control::isActive());
}

void setup() {
    delay(2000); // Aguarda a serial estabilizar
    UNITY_BEGIN();
    
    RUN_TEST(test_pump_turns_on_below_threshold);
    RUN_TEST(test_pump_hysteresis_logic);
    RUN_TEST(test_sensor_error_forces_pump_off);
    
    UNITY_END();
}

void loop() {
    // Nada no loop para testes
}