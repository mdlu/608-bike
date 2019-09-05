#include <Wire.h>
#include <string.h>
#include <TFT_eSPI.h> // Graphics and font library for ST7735 driver chip
#include <SPI.h>
#include <WiFi.h> //Connect to WiFi Network
#include <ArduinoJson.h>

//Classes
class Button{
  public:
  uint32_t t_of_state_2;
  uint32_t t_of_button_change;
  uint32_t debounce_time;
  uint32_t long_press_time;
  uint8_t pin;
  uint8_t flag;
  bool button_pressed;
  uint8_t state; // This is public for the sake of convenience
  Button(int p) {
    flag = 0;
    state = 0;
    pin = p;
    t_of_state_2 = millis(); //init
    t_of_button_change = millis(); //init
    debounce_time = 10;
    long_press_time = 1000;
    button_pressed = 0;
  }
  void read() {
    uint8_t button_state = digitalRead(pin);
    button_pressed = !button_state;
  }
  int update() {
    read();
    flag = 0;
    if (state==0) {
      if (button_pressed) {
        state = 1;
        t_of_button_change = millis();
      }
    } else if (state==1) {
      if (button_pressed){
        if (millis()-t_of_button_change >= debounce_time){
          state = 2;
          t_of_state_2 = millis();
        }
      }else{
        state = 0;
        t_of_button_change = millis();
      }
    } else if (state==2) {
      if (!button_pressed){
        state = 4;
        t_of_button_change = millis();
      }else if (millis()-t_of_state_2 >= long_press_time){
        state = 3;
      }

    } else if (state==3) {
      if (!button_pressed){
        state = 4;
        t_of_button_change = millis();
      }
    } else if (state==4) {
      if (button_pressed){
        t_of_button_change = millis();
        if (millis()-t_of_state_2 >= long_press_time){
          state = 3;
        }else{
          state = 2;
        }
      }else if (millis()-t_of_button_change >= debounce_time){
        if (millis()-t_of_state_2 >= long_press_time){
          flag = 2;
        }else{
          flag = 1;
        }
        state = 0;
      }
    }
    return flag;
  }
};

//Initializers
TFT_eSPI tft = TFT_eSPI();  //Make instance of TFT object
HardwareSerial gps(2); //instantiate approporiate Serial object for GPS

uint32_t timer; //used for loop timing
const uint16_t LOOP_PERIOD = 50; //period of system

const int BUFFER_LENGTH = 200;  //size of char array we'll use for
char buffer[BUFFER_LENGTH] = {0}; //dump chars into the

int lat_deg; //degrees portion of lattitude
float lat_dm; //latitude decimal minutes
char lat_dir; //latitude direction
int lon_deg; //longitude in degrees
float lon_dm; //longitude decimal minutes
char lon_dir; //longitude direction
int year; //year
int month; //month
int day; //day of month
char global_time_array[12] = {0};
bool valid; //is the data valid
int verify = 0;

// Two buttons on the device. Names should probably be changed.
Button leftButton(16);
Button rightButton(5);

unsigned long recording_timer;  // Timer and period for collecting locations (ms)
unsigned long recording_period = 3000;

// Array for storing locations. Should be a 2d array with latitude and longitude values. Max length of this should be changed.
float locations[10000][2]; //100 locations (lat, lon)
uint8_t currentIX;  // Current empty index to be updated with a location

//WiFi constants and resources:
char mit_network[] = "MIT";
char mit_password[] = "";
char mit_guest_network[] = "MIT GUEST";
char mit_guest_password[] = "";
char network[] = "6s08";
char password[] = "iesc6s08"; //Password for 6.08 Lab. Same as above.
const char USER[] = "gduffy-tests"; //Again, need a way to input this.

const int RESPONSE_TIMEOUT = 6000; //ms to wait for response from host
const uint16_t IN_BUFFER_SIZE = 1000; //size of buffer to hold HTTP request
const uint16_t OUT_BUFFER_SIZE = 1000; //size of buffer to hold HTTP response
char request_buffer[IN_BUFFER_SIZE]; //char array buffer to hold HTTP request
char response_buffer[OUT_BUFFER_SIZE]; //char array buffer to hold HTTP response


//Trip timing variables
char start_time[12] = {0};
char end_time[12] = {0};

// Function definitions
void extract(char* data_array){
  // Get important data from GPS string.
  // Doesn't change lat, lon, time values if GPS string is invalid.
  // Variable valid stores whether a good reading was produced.
//  if (strstr(data_array, "A") != NULL){

  // extract is called by GNRMC in every cycle during a trip.

  if (data_array[18] == 'A'){
    valid = true;
  }
  else {
    valid = false;
    return;
  }
  char* parsed = strtok(data_array, ",");
  int ix = 0;
  while (parsed != NULL){
    switch(ix){
      case 0:
        break;
      case 1:
        sprintf(global_time_array,parsed);
        break;
      case 2:
        break;
      case 3:
        parseLat(parsed);
        break;
      case 4:
        lat_dir = *parsed;
        break;
      case 5:
        parseLon(parsed);
        break;
      case 6:
        lon_dir = *parsed;
        break;
      case 9:
        parseDate(parsed);
        break;
      default:
        break;
    }
    parsed = strtok(NULL, ",");
    ix++;
  }
}
    // Functions to parse out data from GPS string
void parseDate(char* date_chars){
  char num[2];
  strncpy(num, date_chars, 2);
  day = atoi(num);

  char num2[2];
  strncpy(num2, date_chars+2, 2);
  month = atoi(num2);

  char num3[2];
  strncpy(num3, date_chars+4, 2);
  year = atoi(num3);
}
void parseLat(char* lat_chars){
  char latnum[2];
  strncpy(latnum, lat_chars, 2);
  lat_deg = atoi(latnum);
  char latnum2[7];
  strncpy(latnum2, lat_chars+2, 7);
  lat_dm = atof(latnum2);
}
void parseLon(char* lon_chars){
  char num[2];
  strncpy(num, lon_chars, 3);
  lon_deg = atoi(num);
  char num2[8];
  strncpy(num2, lon_chars+3, 7);
  lon_dm = atof(num2);

}

// void parseTime(char* time_chars){
//
//   //parseTime takes the time characters from the GPS as an input and places them
//   //into the global variables hour, minute and second respectively. It returns nothing.
//
//   char num[3];
//   strncpy(num, time_chars, 2);
//   hour = atoi(num);
//   char num2[3];
//   strncpy(num2, time_chars+2, 2);
//   minute = atoi(num2);
//   char num3[3];
//   strncpy(num3, time_chars+4, 2);
//   second = atoi(num3);
// }

void extractGNRMC(){
  // Gets GPS string and sends it to be parsed into useful info.
  while (gps.available()) {     // If anything comes in Serial1 (pins 0 & 1)
    gps.readBytesUntil('\n', buffer, BUFFER_LENGTH); // read it and send it out Serial (USB)
    char* info = strstr(buffer,"GNRMC");
    if (info!=NULL){
      Serial.println(buffer);
      extract(buffer);
    }
  }
}

float ddm_to_decimal(int degree, float dm, char dir){
  // Converts format degree decimal_minutes (d*d.d') to decimal degress (d.d*)
  float res = degree+(dm/60);
  if(dir == 'S' or dir == 'W') return -1*res;
  return res;
}

void record_location(){
  // Pings GPS for data, parses latitude and longitude, inserts them into the array of locations, and updates the index of the locations.
  extractGNRMC();
  float latitude = ddm_to_decimal(lat_deg, lat_dm, lat_dir);
  float longitude = ddm_to_decimal(lon_deg, lon_dm, lon_dir);
  Serial.println(latitude);
  Serial.println(longitude);

  if(different_coord(latitude, longitude)){ // Dont record coords in same place

  locations[currentIX][0] = latitude;
  locations[currentIX][1] = longitude;
  currentIX++;
  }
  Serial.println(currentIX);
}

bool different_coord(float lat_, float lon_){
  // check if coordinates are repeated
  float lat_diff = lat_-locations[currentIX-1][0];
  float lon_diff = lon_-locations[currentIX-1][1];
  float delta = .00003;
  if(lat_diff<0) lat_diff*=-1;
  if(lon_diff<0) lon_diff*=-1;
  return ((lat_diff >= delta) || (lon_diff >= delta));
}

  // Functions to change display on ESP
void display_menu(){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  tft.println("Press left button to record a new route.\n\nPress right button to upload the last recorded route.\n\nLong press right button to connect wifi.");
}
void display_getting_fix(){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  tft.println("Getting Fix...");
}
void display_verifying(){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  tft.println("Verifying. Please remain stationary...");
}
void display_recording(){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  tft.println("Recording route. Press left button to end trip.");
}
void display_ending(){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  tft.println("Saving route...");
}
void display_uploading(){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  tft.println("Uploading route...");
}
void display_connecting(char* network){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  char ins[50] = "Connecting to ";
  strncat(ins, network, 25); strcat(ins, "...");
  tft.println(ins);
}
void display_wifi_status(){
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0,0);
  if(WiFi.isConnected()) tft.println("Wifi connected.");
  else tft.println("Wifi not connected.");
  tft.setCursor(0,10);
  tft.println("Press button to exit");
}

// void record_time(char timeVar){
//   * timeVar = global_time_array;
// }

// State machine definitions
uint8_t wifi_state;
uint8_t display_state;  // variable for ESP state machine

#define IDLE 0
#define GETTING_FIX 2
#define RECORDING 3
#define ENDING_TRIP 4
#define WIFI_CONNECT 5
#define SHOW_RESULT 6
#define TO_IDLE 7
#define UPLOADING 8
#define NOT_CONNECTED 9
#define VERIFYING 10

//State Machines
void display_(){
  switch(display_state){
    case IDLE:{
      if(leftButton.update()){
        // Begin recording trip
        currentIX = 0;  // Reset locations index
        memset(locations, 0, sizeof(locations));
        display_getting_fix();
        display_state = GETTING_FIX;
      }
      int r = rightButton.update();
      if(r==1) display_state = UPLOADING;
      else if(r==2) display_state = WIFI_CONNECT;
      break;}

    case GETTING_FIX:
      extractGNRMC();
      if(valid){    // If GPS has a fix, begin recording
        display_verifying();
        sprintf(start_time,global_time_array); //Record start time
        display_state = VERIFYING;
        record_location();
      }
      break;
    case VERIFYING:{
      if (millis()-recording_timer>recording_period){
        extractGNRMC();
        float latitude = ddm_to_decimal(lat_deg, lat_dm, lat_dir);
        float longitude = ddm_to_decimal(lon_deg, lon_dm, lon_dir);
        Serial.println(different_coord(latitude,longitude));
        recording_timer = millis();
        if (!different_coord(latitude, longitude)){
          verify++;
          Serial.print("Verified ");
          Serial.print(verify);
          Serial.println("...");
        }
        else {
          verify = 0;
          Serial.println("Couldn't verify, resetting...");
        }
        if (verify >= 5){
          display_recording();
          display_state = RECORDING;
        }
      }
      break;
      }
    case RECORDING:
      if(leftButton.update()){  // End the trip
        record_location();
        display_ending();
        sprintf(end_time,global_time_array); //Record end time
        display_state = ENDING_TRIP;
      }
      else if(millis()-recording_timer>recording_period){ // Record after a time period
        recording_timer = millis();
        record_location();
      }
      break;
    case ENDING_TRIP:
      display_state = TO_IDLE;
      break;
    case UPLOADING:
      if(!WiFi.isConnected()){
//        display_connecting();
        connect_to_wifi();
      }
      display_uploading();
      upload();
      display_state = SHOW_RESULT;
      break;
    case WIFI_CONNECT:
//      display_connecting();
      connect_to_wifi();
      display_wifi_status();
      display_state = SHOW_RESULT;
      break;
    case SHOW_RESULT:
      if(leftButton.update() || rightButton.update()) display_state = TO_IDLE;
      break;
    case TO_IDLE:
      display_menu();
      display_state = IDLE;
      break;
  }
}

void connect_to_wifi(){
  // Runs through a list of networks and passwords, attempting to connect. Returns if already connected.
  char* wifis[] = {mit_network, mit_password, mit_guest_network, mit_guest_password, network, password};
  for(int ix=0; ix<3; ix++){
    if(WiFi.isConnected()) break;
    display_connecting(wifis[2*ix]);
    attempt_wifi_connection(wifis[2*ix], wifis[2*ix+1]);
  }
}

void attempt_wifi_connection(char* network, char* password){
  // return if already connected
  if (WiFi.isConnected()) return;

  WiFi.begin(network,password); //attempt to connect to wifi
  uint8_t count = 0; //count used for Wifi check times
  Serial.print("Attempting to connect to ");
  Serial.println(network);
  while (WiFi.status() != WL_CONNECTED && count<12) {
    delay(500);
    Serial.print(".");
    count++;
  }
  delay(2000);
  if (WiFi.isConnected()) { //if we connected then print our IP, Mac, and SSID we're on
    Serial.println("CONNECTED!");
    Serial.println(WiFi.localIP().toString() + " (" + WiFi.macAddress() + ") (" + WiFi.SSID() + ")");
    delay(500);
  } else { //if we failed to connect just Try again.
    Serial.println("Failed to Connect :/  ");
    Serial.println(WiFi.status());
    // ESP.restart();
    //Original code restarted the ESP here if WiFi didn't connect. Don't think we want that.
  }
}



void upload(){
  // Moved to its own function
//  connect_to_wifi();

  char body[2000]; //for body;
  char locationstr[2000];
  int capacity = currentIX*JSON_ARRAY_SIZE(2) + JSON_ARRAY_SIZE(currentIX);
  DynamicJsonDocument gpsData(capacity);
//  StaticJsonDocument<512> gpsData;

  copyArray(locations, gpsData.to<JsonArray>()); //For questions, review the ArduinoJson documentation
  serializeJson(gpsData, Serial); //Print to serial monitor for debugging purposes
  serializeJson(gpsData, locationstr);

  sprintf(body,"user=%s&route=%s&start=%s&end=%s",USER,locationstr,start_time,end_time);//generate body, posting to User, 1 step
  int body_len = strlen(body); //calculate body length (for header reporting)
  sprintf(request_buffer,"POST http://608dev.net/sandbox/sc/rtliu/api/bike_server.py HTTP/1.1\r\n");
  strcat(request_buffer,"Host: 608dev.net\r\n");
  strcat(request_buffer,"Content-Type: application/x-www-form-urlencoded\r\n");
  sprintf(request_buffer+strlen(request_buffer),"Content-Length: %d\r\n", body_len); //append string formatted to end of request buffer
  strcat(request_buffer,"\r\n"); //new line from header to body
  strcat(request_buffer,body); //body
  strcat(request_buffer,"\r\n"); //header
  Serial.println(request_buffer);
  do_http_request("608dev.net", request_buffer, response_buffer, OUT_BUFFER_SIZE, RESPONSE_TIMEOUT,true);
//  tft.fillScreen(TFT_BLACK); //fill background
//  tft.setCursor(0,0,1); // set the cursor
  tft.println(response_buffer); //print the result

}


//ESP Code
void setup() {
  Serial.begin(115200);

  tft.init(); //initialize the screen
  tft.setRotation(2); //set rotation for our layout
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);

  pinMode(16, INPUT_PULLUP);
  pinMode(5, INPUT_PULLUP);

  gps.begin(9600,SERIAL_8N1,32,33);
  display_menu();
  timer=millis();
}

void loop() {

  display_();

  while(millis()-timer<LOOP_PERIOD);//pause
  timer = millis();
}
