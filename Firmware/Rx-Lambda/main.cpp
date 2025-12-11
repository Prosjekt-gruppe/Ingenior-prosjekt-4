#include <Arduino.h>
#include <RadioLib.h>

// Lambda80 / SX1280 til ESP32
static const int SX_CS   = 5;
static const int SX_DIO1 = 26;
static const int SX_RST  = 25;
static const int SX_BUSY = 27;

// Samme moduldefinisjon som TX-testen
SX1280 radio = new Module(SX_CS, SX_DIO1, SX_RST, SX_BUSY);

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("=== SX1280 RX LoRa-test ===");

  // Start VSPI på default-pinner (SCK=18, MISO=19, MOSI=23)
  SPI.begin();

  int16_t state = radio.begin(2420.0, 812.5, 9, 7, 15);
  Serial.print("RSSI idle: ");
  Serial.println(radio.getRSSI());



  Serial.print("radio.begin() -> ");
  Serial.println(state);

  if (state != RADIOLIB_ERR_NONE) {
    Serial.println("Radio init feilet, stopper.");
    while (true) { delay(1000); }
  }

  Serial.println("Radio OK! Venter på pakker...");
}

void loop() {
  String str;
  int16_t state = radio.receive(str);
  Serial.print("Idle RSSI: ");
  Serial.println(radio.getRSSI());


  if (state == RADIOLIB_ERR_NONE) {
    Serial.print("Mottatt: '");
    Serial.print(str);
    Serial.println("'");

    Serial.print("RSSI=");
    Serial.print(radio.getRSSI());
    Serial.print(" dBm, SNR=");
    Serial.print(radio.getSNR());
    Serial.println(" dB");

    Serial.println("--------------------------");
  }

  // Ingen else, ingen feilmelding – RX bare lytter stille
}
