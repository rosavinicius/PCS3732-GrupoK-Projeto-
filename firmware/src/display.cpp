#include "display.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

namespace display {

static Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
static bool available = false;

// histórico circular de umidade
static const int HISTORY_LEN = 40;
static float history[HISTORY_LEN];
static int historyCount = 0;
static int historyIndex = 0;

void begin() {
    Wire.begin(OLED_SDA, OLED_SCL);
    available = oled.begin(
        SSD1306_SWITCHCAPVCC,
        OLED_ADDR
    );

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

        int idx =
            (oldestIndex + i)
            % HISTORY_LEN;


        float value =
            constrain(history[idx], 0.0f, 100.0f);


        int plotX =
            x + 1 +
            (int)(
                (float)i /
                (HISTORY_LEN - 1)
                *
                (w - 2)
            );


        int plotY =
            y + h - 1 -
            (int)(
                value /
                100.0f *
                (h - 2)
            );


        if (prevPlotX >= 0) {

            oled.drawLine(
                prevPlotX,
                prevPlotY,
                plotX,
                plotY,
                SSD1306_WHITE
            );
        }


        prevPlotX = plotX;
        prevPlotY = plotY;
    }
}



void update(
    const String& plantId,
    const sensors::Reading& reading,
    float threshold,
    bool pumpActive,
    bool mqttConnected
) {

    pushHistory(reading.humidity);


    if (!available)
        return;


    oled.clearDisplay();
    oled.setCursor(0,0);


    // identificação da planta
    oled.printf(
        "ID: %s\n",
        plantId.c_str()
    );


    oled.printf(
        "Umid: %.0f%% T:%.0f%%\n",
        reading.humidity,
        threshold
    );


    if (!isnan(reading.temperature)) {

        oled.printf(
            "Temp: %.1f C\n",
            reading.temperature
        );

    } else {

        oled.println("Temp: --");
    }


    oled.printf(
        "Pump:%s MQTT:%s\n",
        pumpActive ? "ON" : "OFF",
        mqttConnected ? "OK" : "--"
    );


    drawSparkline(
        0,
        32,
        OLED_WIDTH,
        32
    );


    oled.display();
}


}