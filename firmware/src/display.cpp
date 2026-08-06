#include "display.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

namespace display {

static Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
static bool available = false;

// pequeno histórico circular só para desenhar a série temporal na telinha
static const int HISTORY_LEN = 40;
static float history[HISTORY_LEN];
static int historyCount = 0;
static int historyIndex = 0;

void begin() {
    Wire.begin();
    available = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);

    if (!available) {
        Serial.println("[display] OLED não encontrado, seguindo sem tela");
        return;
    }

    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    oled.setTextSize(1);
    oled.setCursor(0, 0);
    oled.println("Iniciando...");
    oled.display();
}

static void pushHistory(float humidity) {
    if (isnan(humidity)) return;
    history[historyIndex] = humidity;
    historyIndex = (historyIndex + 1) % HISTORY_LEN;
    if (historyCount < HISTORY_LEN) historyCount++;
}

static void drawSparkline(int x, int y, int w, int h) {
    if (historyCount < 2) return;

    oled.drawRect(x, y, w, h, SSD1306_WHITE);

    int oldestIndex = (historyIndex - historyCount + HISTORY_LEN) % HISTORY_LEN;
    int prevPlotX = -1, prevPlotY = -1;

    for (int i = 0; i < historyCount; i++) {
        int idx = (oldestIndex + i) % HISTORY_LEN;
        float value = constrain(history[idx], 0.0f, 100.0f);

        int plotX = x + 1 + (int)((float)i / (HISTORY_LEN - 1) * (w - 2));
        int plotY = y + h - 1 - (int)(value / 100.0f * (h - 2));

        if (prevPlotX >= 0) {
            oled.drawLine(prevPlotX, prevPlotY, plotX, plotY, SSD1306_WHITE);
        }
        prevPlotX = plotX;
        prevPlotY = plotY;
    }
}

void update(const sensors::Reading& reading, float threshold, bool pumpActive, bool mqttConnected) {
    pushHistory(reading.humidity);

    if (!available) return; // sem tela conectada, apenas segue o histórico em memória

    oled.clearDisplay();
    oled.setCursor(0, 0);

    oled.printf("Umid: %.0f%%  Alvo: %.0f%%\n", reading.humidity, threshold);

    if (!isnan(reading.temperature)) {
        oled.printf("Temp: %.1fC   PH: %.1f\n", reading.temperature, reading.ph);
    } else {
        oled.printf("Temp: --      PH: %.1f\n", reading.ph);
    }

    oled.printf("Bomba: %s  MQTT: %s\n",
                pumpActive ? "LIGADA" : "off",
                mqttConnected ? "ok" : "--");

    drawSparkline(0, 28, OLED_WIDTH, 34);

    oled.display();
}

} // namespace display