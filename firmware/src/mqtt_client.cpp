#include "mqtt_client.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"

namespace mqtt_client {

static WiFiClient wifiClient;
static PubSubClient client(wifiClient);
static String deviceId;
static String topicStatus, topicSensors, topicConfig, topicPump;
static ConfigCallback configCallback = nullptr;
static unsigned long lastReconnectAttempt = 0;

static void handleMessage(char* topic, byte* payload, unsigned int length) {
    if (String(topic) != topicConfig) return;

    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload, length);
    if (err) {
        Serial.printf("[mqtt] config JSON inválido: %s\n", err.c_str());
        return;
    }

    if (doc["humidityThreshold"].is<float>()) {
        float value = doc["humidityThreshold"];
        Serial.printf("[mqtt] novo threshold recebido: %.1f%%\n", value);
        if (configCallback) configCallback(value);
    }
}

void publishOnlineStatus() {
    JsonDocument doc;
    doc["status"] = "online";
    doc["name"] = deviceId;

    char buf[128];
    size_t n = serializeJson(doc, buf);
    client.publish(topicStatus.c_str(), (const uint8_t*)buf, n, /* retained = */ true);
}

static bool reconnect() {
    Serial.printf("[mqtt] conectando em %s:%d como %s...\n",
                  MQTT_BROKER_HOST, MQTT_BROKER_PORT, deviceId.c_str());

    // LWT: se a conexão cair sem aviso (queda de energia/WiFi), o broker
    // publica esta mensagem retained automaticamente.
    JsonDocument lwtDoc;
    lwtDoc["status"] = "offline";
    lwtDoc["name"] = deviceId;
    char lwtBuf[128];
    size_t lwtLen = serializeJson(lwtDoc, lwtBuf);

    bool connected = client.connect(
        deviceId.c_str(),
        nullptr, nullptr,               // usuário/senha do broker, se configurado
        topicStatus.c_str(), 1, true,   // tópico, QoS, retained do LWT
        lwtBuf
    );

    if (connected) {
        Serial.println("[mqtt] conectado");
        publishOnlineStatus();
        client.subscribe(topicConfig.c_str());
    } else {
        Serial.printf("[mqtt] falha, rc=%d\n", client.state());
    }

    return connected;
}

void begin(const String& id, ConfigCallback onConfig) {
    deviceId = id;
    configCallback = onConfig;

    topicStatus  = String(TOPIC_PREFIX) + deviceId + "/status";
    topicSensors = String(TOPIC_PREFIX) + deviceId + "/sensors";
    topicConfig  = String(TOPIC_PREFIX) + deviceId + "/config";
    topicPump    = String(TOPIC_PREFIX) + deviceId + "/pump";

    client.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    client.setCallback(handleMessage);
    client.setBufferSize(256);
}

void poll() {
    if (!client.connected()) {
        unsigned long now = millis();
        if (now - lastReconnectAttempt > MQTT_RECONNECT_MS) {
            lastReconnectAttempt = now;
            reconnect();
        }
        return;
    }
    client.loop();
}

bool isConnected() {
    return client.connected();
}

void publishSensorReading(const sensors::Reading& reading) {
    if (!client.connected()) return;

    JsonDocument doc;
    doc["humidity"] = serialized(String(reading.humidity, 1));
    if (!isnan(reading.temperature)) {
        doc["temperature"] = serialized(String(reading.temperature, 1));
    }
    doc["ts"] = (uint64_t)millis(); // o backend normaliza pra timestamp real ao receber

    char buf[192];
    size_t n = serializeJson(doc, buf);
    client.publish(topicSensors.c_str(), (const uint8_t*)buf, n, /* retained = */ false);
}

void publishPumpStatus(bool active) {
    if (!client.connected()) return;

    JsonDocument doc;
    doc["active"] = active;

    char buf[64];
    size_t n = serializeJson(doc, buf);
    client.publish(topicPump.c_str(), (const uint8_t*)buf, n, /* retained = */ true);
}

} // namespace mqtt_client