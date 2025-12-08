#include <Arduino.h>
#include <RadioLib.h>

// ----------- SX1280 / Lambda80 wiring ----------
static const int SX_CS   = 5;
static const int SX_DIO1 = 26;
static const int SX_RST  = 25;
static const int SX_BUSY = 27;

// ESP32 hardware SPI: SCK=18, MISO=19, MOSI=23

SX1280 radio = new Module(SX_CS, SX_DIO1, SX_RST, SX_BUSY);

// ----------- CRSF UART to FC ----------
#define CRSF_SERIAL   Serial1
static const int CRSF_TX_PIN = 17;   // ESP32 TX to FC RX
static const int CRSF_RX_PIN = 16;   // not really used, but needed for begin()

// ----------- Link packets -------------
static const uint8_t CTRL_SYNC  = 0xA5;
static const uint8_t TELE_SYNC  = 0x5A;
static const size_t  CTRL_LEN   = 12;
static const size_t  TELE_LEN   = 8;

// running stats for link quality
static uint32_t g_totalFrames = 0;
static uint32_t g_goodFrames  = 0;

// --- CRC-8 for link packets (poly 0x8C, simple) ---
uint8_t linkCrc8(const uint8_t* data, uint8_t len) {
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

// --- CRC-8 DVB-S2 for CRSF (poly 0xD5, MSB-first) ---
uint8_t crsfCrc(const uint8_t* data, uint8_t len) {
  uint8_t crc = 0;
  while (len--) {
    crc ^= *data++;
    for (uint8_t i = 0; i < 8; i++) {
      if (crc & 0x80) {
        crc = (crc << 1) ^ 0xD5;
      } else {
        crc <<= 1;
      }
    }
  }
  return crc;
}

// --- map 1000..2000 us -> 0..1984 CRSF ---
uint16_t mapUsToCrsf(int us) {
  if (us < 1000) us = 1000;
  if (us > 2000) us = 2000;
  // center 1500 -> 992
  return (uint16_t)((us - 1000) * 1984L / 1000L);
}

// --- map 0..2047 (our link) -> 1000..2000 us ---
int map11bitToUs(uint16_t v) {
  if (v > 2047) v = 2047;
  return 1000 + (int)(v * 1000L / 2047L);
}

// --- send CRSF RC_CHANNELS_PACKED frame to FC ---
void sendCrsfRcChannels(int rollUs, int pitchUs, int yawUs, int thrUs) {
  uint32_t ch[16];
  ch[0] = mapUsToCrsf(rollUs);
  ch[1] = mapUsToCrsf(pitchUs);
  ch[2] = mapUsToCrsf(yawUs);
  ch[3] = mapUsToCrsf(thrUs);
  // remaining channels at center (992)
  for (int i = 4; i < 16; i++) {
    ch[i] = 992;
  }

  uint8_t payload[22] = {0};
  int bitPos = 0;
  for (int i = 0; i < 16; i++) {
    uint16_t v = (ch[i] > 1984) ? 1984 : (uint16_t)ch[i];
    for (int b = 0; b < 11; b++, bitPos++) {
      if (v & (1 << b)) {
        payload[bitPos >> 3] |= (1 << (bitPos & 7));
      }
    }
  }

  uint8_t frame[26];
  frame[0] = 0xC8;       // to FC
  frame[1] = 24;         // len(type + payload + crc)
  frame[2] = 0x16;       // RC_CHANNELS_PACKED
  memcpy(&frame[3], payload, 22);
  frame[25] = crsfCrc(&frame[2], 1 + 22); // type + payload

  CRSF_SERIAL.write(frame, sizeof(frame));
}

// --- stub: read FC / battery voltage in mV ---
uint16_t readBatteryMv() {
  // TODO: connect ADC to LiPo and implement real read + scaling
  return 11100;  // 11.1 V as placeholder
}

// --- send telemetry back to TX over RF ---
void sendTelemetry() {
  uint8_t buf[TELE_LEN];

  uint16_t batt = readBatteryMv();
  int8_t  rssi  = (int8_t)radio.getRSSI();

  uint8_t lq = 0;
  if (g_totalFrames > 0) {
    lq = (uint8_t)((g_goodFrames * 100UL) / g_totalFrames);
  }

  buf[0] = TELE_SYNC;
  buf[1] = (batt >> 8) & 0xFF;
  buf[2] = batt & 0xFF;
  buf[3] = (uint8_t)rssi;
  buf[4] = lq;
  buf[5] = 0;
  buf[6] = 0;

  buf[7] = linkCrc8(buf, 7);

  int16_t state = radio.transmit(buf, TELE_LEN);
  (void)state;
  radio.startReceive();  // back to RX
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("RX: boot");

  // CRSF UART to FC
  CRSF_SERIAL.begin(420000, SERIAL_8N1, CRSF_RX_PIN, CRSF_TX_PIN);

  // SPI + radio
  SPI.begin(18, 19, 23);
  int16_t state = radio.beginFLRC(
    2440.0,     // MHz
    1300,       // kbps
    1,          // coding rate index (1:0)
    10,         // dBm
    16,         // preamble
    RADIOLIB_SHAPING_0_5
  );
  if (state != RADIOLIB_ERR_NONE) {
    Serial.print("Radio init failed, code "); Serial.println(state);
    while (true) delay(100);
  }

  radio.startReceive();
}

void loop() {
  uint8_t rxBuf[32];

  int16_t state = radio.readData(rxBuf, sizeof(rxBuf));
  if (state == RADIOLIB_ERR_NONE) {
    size_t len = radio.getPacketLength();
    if (len == CTRL_LEN && rxBuf[0] == CTRL_SYNC && linkCrc8(rxBuf, 11) == rxBuf[11]) {
      g_totalFrames++;
      g_goodFrames++;

      uint8_t frame = rxBuf[1];
      uint8_t flags = rxBuf[2];
      (void)frame;
      (void)flags;

      uint16_t c1 = (rxBuf[3]  << 8) | rxBuf[4];
      uint16_t c2 = (rxBuf[5]  << 8) | rxBuf[6];
      uint16_t c3 = (rxBuf[7]  << 8) | rxBuf[8];
      uint16_t c4 = (rxBuf[9]  << 8) | rxBuf[10];

      int rollUs  = map11bitToUs(c1);
      int pitchUs = map11bitToUs(c2);
      int yawUs   = map11bitToUs(c3);
      int thrUs   = map11bitToUs(c4);

      // Debug
      Serial.print("RC us: R "); Serial.print(rollUs);
      Serial.print(" P "); Serial.print(pitchUs);
      Serial.print(" Y "); Serial.print(yawUs);
      Serial.print(" T "); Serial.println(thrUs);

      // Send to FC via CRSF
      sendCrsfRcChannels(rollUs, pitchUs, yawUs, thrUs);

      // Send telemetry back to TX
      sendTelemetry();
    } else {
      g_totalFrames++;
    }

    radio.startReceive();
  } else if (state != RADIOLIB_ERR_RX_TIMEOUT && state != RADIOLIB_ERR_WRONG_MODE) {
    // some other error, restart RX
    Serial.print("RX err "); Serial.println(state);
    radio.startReceive();
  }

  // you can add failsafe logic here based on time since last good frame
}
