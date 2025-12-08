#include <Arduino.h>
#include <RadioLib.h>

// Same wiring & module definition as TX:
SX1280 radio = new Module(5, 27, 26, 25, SPI, SPISettings());

uint8_t rxBuf[32];

// Helpers from above
uint8_t crc8(const uint8_t* data, uint8_t len) {
  uint8_t crc = 0x00;
  while (len--) {
    uint8_t extract = *data++;
    for (uint8_t i = 0; i < 8; i++) {
      uint8_t sum = (crc ^ extract) & 0x01;
      crc >>= 1;
      if(sum) crc ^= 0x8C;
      extract >>= 1;
    }
  }
  return crc;
}

int map11bitToRc(uint16_t v) {
  if (v > 2047) v = 2047;
  return 1000 + (int)(v * 1000L / 2047L);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("RX: Starting RadioLib SX1280...");

  int state = radio.begin();
  if(state != RADIOLIB_ERR_NONE) {
    Serial.print("Radio init failed, code "); Serial.println(state);
    while(true);
  }

  state = radio.beginFLRC(
    2440.0,  // MHz (must match TX)
    1300.0,
    117.0,
    1.0,
    1.0
  );
  if(state != RADIOLIB_ERR_NONE) {
    Serial.print("FLRC config failed, code "); Serial.println(state);
    while(true);
  }

  radio.setOutputPower(10);

  // Start in receive mode
  // RadioLib SX1280: use startReceive() for continuous RX
  radio.startReceive();
}

void loop() {
  // Non-blocking receive
  int state = radio.readData(rxBuf, sizeof(rxBuf));
  if(state == RADIOLIB_ERR_NONE) {
    // We received something - check length and parse
    size_t len = radio.getPacketLength();
    if(len == 12 && rxBuf[0] == 0xA5 && crc8(rxBuf, 11) == rxBuf[11]) {
      uint8_t frame = rxBuf[1];
      uint8_t flags = rxBuf[2];

      uint16_t c1 = (rxBuf[3]  << 8) | rxBuf[4];
      uint16_t c2 = (rxBuf[5]  << 8) | rxBuf[6];
      uint16_t c3 = (rxBuf[7]  << 8) | rxBuf[8];
      uint16_t c4 = (rxBuf[9]  << 8) | rxBuf[10];

      int roll  = map11bitToRc(c1);
      int pitch = map11bitToRc(c2);
      int yaw   = map11bitToRc(c3);
      int thr   = map11bitToRc(c4);

      Serial.print("Frame "); Serial.print(frame);
      Serial.print(" Flags "); Serial.print(flags, BIN);
      Serial.print(" | R:"); Serial.print(roll);
      Serial.print(" P:"); Serial.print(pitch);
      Serial.print(" Y:"); Serial.print(yaw);
      Serial.print(" T:"); Serial.println(thr);
    }

    // Go back to RX
    radio.startReceive();
  }
  else if(state != RADIOLIB_ERR_RX_TIMEOUT && state != RADIOLIB_ERR_NONE) {
    // Some RX error, restart RX
    Serial.print("RX error, code "); Serial.println(state);
    radio.startReceive();
  }

  // You can add a failsafe timer here.
}
