#include "wifi_manager.h"
#include <WiFi.h>
#include "config.h"

namespace wifi_manager {

static unsigned long lastRetryAt = 0;
static String cachedDeviceId;

void begin() {
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false); // reduz latência/perda de pacotes MQTT
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.printf("[wifi] conectando em %s", WIFI_SSID);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
        delay(250);
        Serial.print(".");
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("[wifi] conectado, IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("[wifi] falha ao conectar, vai tentar de novo no loop");
    }
}

void poll() {
    if (WiFi.status() == WL_CONNECTED) return;

    unsigned long now = millis();
    if (now - lastRetryAt < WIFI_RETRY_MS) return;
    lastRetryAt = now;

    Serial.println("[wifi] reconectando...");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

bool isConnected() {
    return WiFi.status() == WL_CONNECTED;
}

String getDeviceId() {
    if (cachedDeviceId.length() > 0) return cachedDeviceId;

    uint64_t mac = ESP.getEfuseMac();
    char buf[13];
    snprintf(buf, sizeof(buf), "%04x%08x",
              (uint16_t)(mac >> 32), (uint32_t)mac);

    cachedDeviceId = String("esp32-") + String(buf).substring(4); // últimos 8 hex chars
    return cachedDeviceId;
}

} // namespace wifi_manager