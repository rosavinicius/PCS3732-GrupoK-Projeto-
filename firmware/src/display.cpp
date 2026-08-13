#include "display.h"

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Arduino.h>

#include "config.h"


namespace display {


static LiquidCrystal_I2C lcd(
    LCD_ADDR,
    16,
    2
);


static bool available = false;


// controla alternância das telas
static unsigned long lastPageChange = 0;
static bool showPlantId = false;

static const unsigned long PAGE_INTERVAL = 3000;



void begin() {

    Serial.println("[display] iniciando LCD 1602...");

    Wire.setPins(LCD_SDA, LCD_SCL);
    Wire.begin();
    delay(1000); // aguarda o barramento estabilizar

    lcd.init();
    lcd.backlight();
    available = true;

    lcd.clear();

    lcd.setCursor(0,0);
    lcd.print("Irrigador");

    lcd.setCursor(0,1);
    lcd.print("Inicializando");

    Serial.println("[display] LCD conectado!");
}




void update(
    const String& plantId,
    const sensors::Reading& reading,
    float threshold,
    bool pumpActive,
    bool mqttConnected
){

    if(!available)
        return;


    unsigned long now = millis();


    if(now - lastPageChange >= PAGE_INTERVAL)
    {
        lastPageChange = now;
        showPlantId = !showPlantId;
    }


    lcd.clear();



    /*
        Tela 1:
        ID da planta
        Status MQTT
    */

    if(showPlantId)
    {

        lcd.setCursor(0,0);

        lcd.print("ID:");
        lcd.print(
            plantId.substring(0,13)
        );


        lcd.setCursor(0,1);

        lcd.print(
            mqttConnected ? "MQTT ONLINE" :
                            "MQTT OFF"
        );

    }



    /*
        Tela 2:
        Sensores e bomba
    */

    else
    {

        lcd.setCursor(0,0);


        lcd.print("U:");
        lcd.print(
            isnan(reading.humidity) ?
            "--" :
            String((int)reading.humidity)
        );

        lcd.print("% ");


        lcd.print("T:");

        if(isnan(reading.temperature))
        {
            lcd.print("--");
        }
        else
        {
            lcd.print(
                (int)reading.temperature
            );
        }


        lcd.print("C");



        lcd.setCursor(0,1);


        if(pumpActive)
            lcd.print("PUMP ON ");
        else
            lcd.print("PUMP OFF");


        lcd.print(" ");


        lcd.print(
            mqttConnected ?
            "OK" :
            "--"
        );

    }

}



}