#include <FastLED.h>
#include <Ethernet.h>
#ifdef __AVR__
 #include <avr/power.h> // Required for 16 MHz Adafruit Trinket
#endif

/* ///////////////
Ethernet settings here
*/ ///////////////
byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED 
};
IPAddress ip(192, 168, 1, 177);
IPAddress myDns(192, 168, 1, 1);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 0, 0);

EthernetServer server(12345);
//////////////////

String messagestr = "";
const unsigned int msg_arrLen = 4;
int msg_array[msg_arrLen] = {-1};


/* ///////////////
LED settings here
*/ ///////////////
bool last_time_on = true;

#define CONTROL_PIN 6
#define EXP_CT 8
#define STRIP_SGMTS 4
#define BLINK_DELAY 500

int col_array[EXP_CT][msg_arrLen-1];

// Adafruit_NeoPixel outdoor(EXP_CT*2, OUTDOOR_PIN, NEO_GRB + NEO_KHZ800);
// Adafruit_NeoPixel indoor(EXP_CT, INDOOR_PIN, NEO_GRB + NEO_KHZ800);

CRGB testleds[EXP_CT * STRIP_SGMTS];
//////////////////

void setup() {
  Serial.begin(9600);
  invalid_array(msg_array, msg_arrLen);
  zero_matrix(col_array, EXP_CT, msg_arrLen-1);

  FastLED.addLeds<WS2812B, CONTROL_PIN, RGB>(testleds, EXP_CT);
  FastLED.setBrightness(255);

  FastLED.clear();
  FastLED.show();

  Ethernet.begin(mac, ip, myDns, gateway, subnet);
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    while (true) {
      delay(1); // do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("Ethernet cable is not connected.");
  }

  // start listening for clients
  server.begin();

  Serial.print("Chat server address:");
  Serial.println(Ethernet.localIP());
}

void loop() {

  EVERY_N_MILLISECONDS(BLINK_DELAY){
    if (last_time_on) {
      FastLED.clear();
      last_time_on = false;
    }
    else{
      for (int segment=0; segment<STRIP_SGMTS; segment++){
        for(int px=0; px<EXP_CT; px++){
              int r = col_array[px][0];
              int g = col_array[px][1];
              int b = col_array[px][2];
              testleds[segment*EXP_CT + px] = CRGB(r, g, b);
      }
      
      
      last_time_on = true;
      }
    }
    FastLED.show();
  }
  
  EthernetClient client = server.available();
  
  if (client) {
    while (client.available() > 0) {
      char thisChar = client.read();
      messagestr += thisChar;
    }

    if (messagestr != ""){
      write_led_array(msg_array, messagestr);
      int position = msg_array[0];
      for (int i=0; i<msg_arrLen-1;i++){
        col_array[position][i] = msg_array[i+1];
      }
    }
    messagestr = "";

    client.write("0");
 }
}

void invalid_array(int array[], int arrlen){
  for(int ii=0;ii<arrlen;ii++){
    array[ii] = -1;
  }
}

void zero_matrix(int array[][msg_arrLen-1], int rows, int cols){
  for(int i=0; i<rows; i++){
    for (int j=0; j<cols; j++){
      array[i][j] = 0;
    }
  }
}

void write_led_array(int array[], String message){
  int strlen = message.length();
  String bufferStr = "";
  int jj = 0;
  for (int i=0; i<strlen; i++){

    char thechar = message.charAt(i);
    if(thechar != ','){
      bufferStr.concat(thechar);
    }

    if(thechar==',' || i==strlen-1){
      array[jj] = bufferStr.toInt();
      bufferStr = "";
      jj += 1;
    }
  }
}