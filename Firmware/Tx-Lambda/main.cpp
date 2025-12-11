#include <Arduino.h>
#include <RadioLib.h>

// Lambda80 / SX1280 til ESP32
static const int SX_CS   = 5;
static const int SX_DIO1 = 26;
static const int SX_RST  = 25;
static const int SX_BUSY = 27;

SX1280 radio = new Module(SX_CS, SX_DIO1, SX_RST, SX_BUSY);

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("=== SX1280 TX LoRa – kontinuerlig test ===");

  // Start VSPI på default-pinnene (SCK=18, MISO=19, MOSI=23)
  SPI.begin();

  // Sett opp pinnene slik at vi kan lese nivåer
  pinMode(SX_CS,   INPUT_PULLUP);
  pinMode(SX_BUSY, INPUT);
  pinMode(SX_RST,  INPUT_PULLUP);

  // Liten init-loop som prøver om igjen helt til det funker
  while (true) {
    Serial.print("CS   = "); Serial.println(digitalRead(SX_CS));
    Serial.print("BUSY = "); Serial.println(digitalRead(SX_BUSY));
    Serial.print("RESET= "); Serial.println(digitalRead(SX_RST));

    int16_t state = radio.begin(2420.0, 812.5, 9, 7, 15);
    Serial.print("RSSI idle: ");
    Serial.println(radio.getRSSI());
// standard LoRa-oppsett

    Serial.print("radio.begin() -> ");
    Serial.println(state);

    if (state == RADIOLIB_ERR_NONE) {
      Serial.println("Radio OK! Starter sendeloop...");
      break;
    }

    Serial.println("Init feilet, prøver igjen om 1 sekund...");
    delay(1000);
  }
}

void loop() {
  static uint32_t counter = 0;
  Serial.print("Idle RSSI: ");
  Serial.println(radio.getRSSI());


  // Lag en liten tekstpakke med teller
  char payload[32];
  snprintf(payload, sizeof(payload), "PKT_%lu", (unsigned long)counter++);

  int16_t txState = radio.transmit(payload);

  Serial.print("Sendte: ");
  Serial.print(payload);
  Serial.print("  -> transmit() = ");
  Serial.println(txState);

  // Ikke flood helt – 5 pakker i sekundet
  delay(200);
}
