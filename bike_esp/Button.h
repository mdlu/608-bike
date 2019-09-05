//{\rtf1\ansi\ansicpg1252\cocoartf1671\cocoasubrtf200
//{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
//{\colortbl;\red255\green255\blue255;}
//{\*\expandedcolortbl;;}
//\margl1440\margr1440\vieww10800\viewh8400\viewkind0
//\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0
//
//\f0\fs24 \cf0 #ifndef Button_h\
//#define Button_h\
//#include \'93Arduino.h\'94\
//\
//class Button\{ \
//public: \
//uint32_t t_of_state_2; \
//uint32_t t_of_button_change; uint32_t debounce_time; uint32_t long_press_time; uint8_t pin; uint8_t flag; bool button_pressed; uint8_t state; // This is public for the sake of convenience Button(int p) \{ flag = 0; state = 0; pin = p; t_of_state_2 = millis(); //init t_of_button_change = millis(); //init debounce_time = 10; long_press_time = 1000; button_pressed = 0; \} void read() \{ uint8_t button_state = digitalRead(pin); button_pressed = !button_state; \} int update() \{ read(); flag = 0; //your code here!<------!!!! return flag; \} \}; Button button(BUTTON_PIN); void setup() \{ Serial.begin(115200); // Set up serial port pinMode(BUTTON_PIN, INPUT_PULLUP); tft.init(); tft.setRotation(2); tft.setTextSize(1); tft.fillScreen(TFT_BLACK); \}\
//\
//#endif}
