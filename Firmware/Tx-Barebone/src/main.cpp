#include <Arduino.h>
#include <RadioLib.h>

// SX1280 wiring for Lambda80 on ESP32
// SX1280(nss, busy, dio1, reset, sclk, miso, mosi)
SX1280 radio = new Module(5, 27, 26, 25, SPI, SPISettings()); 

uint8_t txBuf[12];
uint8_t frameCounter = 0;

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

uint16_t mapRcTo11bit(int v) {
  if (v < 1000) v = 1000;
  if (v > 2000) v = 2000;
  return (uint16_t)((v - 1000) * 2047L / 1000L);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("TX: Starting RadioLib SX1280...");

  // init radio
  int state = radio.begin();
  if(state != RADIOLIB_ERR_NONE) {
    Serial.print("Radio init failed, code "); Serial.println(state);
    while(true);
  }

  // Set frequency to 2.44 GHz, FLRC @ ~1.3 Mbps, 125 kHz BW, coding 1:0
  // Params: freq (MHz), bitrate (kbps), bandwidth (kHz), codingRate, shaping
  // For SX1280 in RadioLib, use beginFLRC variant:
  state = radio.beginFLRC(
    2440.0,         // freq MHz
    1300.0,         // bitrate kbps
    117.0,          // bandwidth kHz (approx; use closest supported)
    1.0,            // coding rate (1:0)
    1.0             // BT shaping
  );
  if(state != RADIOLIB_ERR_NONE) {
    Serial.print("FLRC config failed, code "); Serial.println(state);
    while(true);
  }

  // Set output power (dBm), 0–13 typical
  radio.setOutputPower(10);

  // Optional: set sync word length, preamble, CRC, whitening etc if needed
  // RadioLib uses sensible defaults for FLRC.
}

void buildPacket() {
  // TODO: replace these with actual stick reads
  int roll  = 1500;
  int pitch = 1500;
  int yaw   = 1500;
  int thr   = 1200;

  uint16_t c1 = mapRcTo11bit(roll);
  uint16_t c2 = mapRcTo11bit(pitch);
  uint16_t c3 = mapRcTo11bit(yaw);
  uint16_t c4 = mapRcTo11bit(thr);

  txBuf[0] = 0xA5;
  txBuf[1] = frameCounter++;
  txBuf[2] = 0x00;   // flags

  txBuf[3]  = (c1 >> 8) & 0xFF;
  txBuf[4]  =  c1       & 0xFF;
  txBuf[5]  = (c2 >> 8) & 0xFF;
  txBuf[6]  =  c2       & 0xFF;
  txBuf[7]  = (c3 >> 8) & 0xFF;
  txBuf[8]  =  c3       & 0xFF;
  txBuf[9]  = (c4 >> 8) & 0xFF;
  txBuf[10] =  c4       & 0xFF;

  txBuf[11] = crc8(txBuf, 11);
}

void loop() {
  buildPacket();

  int state = radio.transmit(txBuf, sizeof(txBuf));
  if(state != RADIOLIB_ERR_NONE) {
    Serial.print("TX failed, code "); Serial.println(state);
  }

  // ~250 Hz
  delay(4);
}
