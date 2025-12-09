#include <Arduino.h>
#include <RadioLib.h>

/* ============================================================
   Hardware Configuration
   ============================================================ */

// SX1280 radio (Lambda80)
static const int PIN_CS   = 5;
static const int PIN_DIO1 = 26;
static const int PIN_RST  = 25;
static const int PIN_BUSY = 27;

// UART to Betaflight flight controller
#define FC_SERIAL      Serial1
static const int PIN_FC_TX = 17;   // ESP32 TX → FC RX
static const int PIN_FC_RX = 16;   // ESP32 RX ← FC TX

// Create radio instance (RadioLib)
SX1280 radio = new Module(PIN_CS, PIN_DIO1, PIN_RST, PIN_BUSY);

/* ============================================================
   Protocol Definitions
   ============================================================ */

// RF packet sync bytes
const uint8_t SYNC_CONTROL  = 0xA5;
const uint8_t SYNC_TELEMETRY = 0x5A;

// RF packet sizes
const size_t CONTROL_PACKET_LEN = 12;
const size_t TELEMETRY_PACKET_LEN = 8;

// CRSF constants
const uint8_t CRSF_ADDR_FC       = 0xC8;
const uint8_t CRSF_TYPE_RC       = 0x16;   // RC_CHANNELS_PACKED
const uint8_t CRSF_TYPE_BATTERY  = 0x08;   // Battery sensor (voltage)

/* ============================================================
   Global State
   ============================================================ */

uint32_t totalFrames = 0;
uint32_t goodFrames  = 0;

// FC telemetry state
uint16_t fcBatteryMv = 0;   // updated from CRSF telemetry

// CRSF telemetry parsing buffer
uint8_t  crsfBuf[64];
uint8_t  crsfPtr = 0;
uint8_t  crsfExpectedLength = 0;

/* ============================================================
   Utility Functions
   ============================================================ */

// --- Custom RF CRC (0x8C polynomial) ---
uint8_t crcRF(const uint8_t *data, uint8_t len) {
  uint8_t crc = 0;
  while (len--) {
    uint8_t in = *data++;
    for (uint8_t i = 0; i < 8; i++) {
      uint8_t mix = (crc ^ in) & 0x01;
      crc >>= 1;
      if (mix) crc ^= 0x8C;
      in >>= 1;
    }
  }
  return crc;
}

// --- CRSF CRC (official DVB-S2 polynomial 0xD5) ---
uint8_t crcCRSF(const uint8_t *data, uint8_t len) {
  uint8_t crc = 0;
  while (len--) {
    crc ^= *data++;
    for (uint8_t i = 0; i < 8; i++) {
      crc = (crc & 0x80) ? (crc << 1) ^ 0xD5 : (crc << 1);
    }
  }
  return crc;
}

// --- Convert RF 0..2047 -> 1000..2000 µs ---
int rfToUs(uint16_t v) {
  v = min(v, (uint16_t)2047);
  return 1000 + (v * 1000L / 2047L);
}

// --- Convert Betaflight RC us → CRSF channel value (0..1984) ---
uint16_t usToCrsf(int us) {
  us = constrain(us, 1000, 2000);
  return (us - 1000) * 1984L / 1000L;
}

/* ============================================================
   CRSF: RC Output → Flight Controller
   ============================================================ */

void sendCRSF_RC(int rollUs, int pitchUs, int yawUs, int thrUs) {
  uint32_t ch[16];

  // Map 4 channels
  ch[0] = usToCrsf(rollUs);
  ch[1] = usToCrsf(pitchUs);
  ch[2] = usToCrsf(yawUs);
  ch[3] = usToCrsf(thrUs);

  // Pad remaining channels to center
  for (int i = 4; i < 16; i++) {
    ch[i] = 992;
  }

  // Pack into CRSF 22-byte payload
  uint8_t payload[22] = {0};
  int bitIndex = 0;

  for (int i = 0; i < 16; i++) {
    uint16_t val = min(ch[i], (uint32_t)1984);
    for (int b = 0; b < 11; b++, bitIndex++) {
      if (val & (1 << b)) {
        payload[bitIndex >> 3] |= (1 << (bitIndex & 7));
      }
    }
  }

  // Build CRSF frame
  uint8_t frame[26];
  frame[0] = CRSF_ADDR_FC;
  frame[1] = 24;                // length = type + payload + crc
  frame[2] = CRSF_TYPE_RC;
  memcpy(&frame[3], payload, 22);
  frame[25] = crcCRSF(&frame[2], 23);

  FC_SERIAL.write(frame, sizeof(frame));
}

/* ============================================================
   CRSF: Telemetry Input ← Flight Controller
   ============================================================ */

void parseCRSFByte(uint8_t b) {

  // Stage 1: waiting for sync (0xC8)
  if (crsfPtr == 0) {
    if (b == CRSF_ADDR_FC) {   // FC → receiver uses same address
      crsfBuf[crsfPtr++] = b;
    }
    return;
  }

  // Stage 2: store byte
  crsfBuf[crsfPtr++] = b;

  // Capture frame length (2nd byte)
  if (crsfPtr == 2) {
    crsfExpectedLength = b;
  }

  // If we have the complete frame:
  if (crsfPtr == crsfExpectedLength + 2) {
    uint8_t type = crsfBuf[2];

    // Only battery telemetry for now
    if (type == CRSF_TYPE_BATTERY) {
      uint16_t volts_x100 = (crsfBuf[3] << 8) | crsfBuf[4]; // 0.01V units
      fcBatteryMv = volts_x100 * 10;                        // convert → millivolts
    }

    // Reset parser
    crsfPtr = 0;
    crsfExpectedLength = 0;
  }
}

void pollFlightControllerTelemetry() {
  while (FC_SERIAL.available()) {
    parseCRSFByte(FC_SERIAL.read());
  }
}

/* ============================================================
   RF Telemetry (RX → TX)
   ============================================================ */

void sendRF_Telemetry() {
  uint8_t buf[TELEMETRY_PACKET_LEN];

  uint16_t batt = (fcBatteryMv > 0) ? fcBatteryMv : 11100;
  int8_t   rssi = radio.getRSSI();
  uint8_t  lq   = (totalFrames > 0) ? (100UL * goodFrames / totalFrames) : 0;

  buf[0] = SYNC_TELEMETRY;
  buf[1] = batt >> 8;
  buf[2] = batt & 0xFF;
  buf[3] = rssi;
  buf[4] = lq;
  buf[5] = 0;
  buf[6] = 0;
  buf[7] = crcRF(buf, 7);

  radio.transmit(buf, TELEMETRY_PACKET_LEN);
  radio.startReceive();
}

/* ============================================================
   Setup
   ============================================================ */

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("RX: Starting...");

  // FC UART (CRSF)
  FC_SERIAL.begin(420000, SERIAL_8N1, PIN_FC_RX, PIN_FC_TX);

  // Radio SPI bus
  SPI.begin(18, 19, 23);

  // Init SX1280 with FLRC parameters
  int16_t err = radio.beginFLRC(
    2440.0,                 // MHz
    1300,                  // kbps
    1,                     // coding rate index
    10,                    // TX power (dBm)
    16,                    // preamble
    RADIOLIB_SHAPING_0_5
  );

  if (err != RADIOLIB_ERR_NONE) {
    Serial.print("SX1280 init failed: ");
    Serial.println(err);
    while (true) delay(100);
  }

  radio.startReceive();
}

/* ============================================================
   Main Loop
   ============================================================ */

void loop() {

  // Step 1: Read telemetry from Betaflight (UART → CRSF)
  pollFlightControllerTelemetry();

  // Step 2: Check for RF control packet
  uint8_t rxBuf[32];
  int16_t state = radio.readData(rxBuf, sizeof(rxBuf));

  if (state == RADIOLIB_ERR_NONE) {

    size_t len = radio.getPacketLength();
    bool packetOK =
      (len == CONTROL_PACKET_LEN) &&
      (rxBuf[0] == SYNC_CONTROL) &&
      (crcRF(rxBuf, 11) == rxBuf[11]);

    totalFrames++;

    if (packetOK) {
      goodFrames++;

      uint16_t roll  = (rxBuf[3] << 8) | rxBuf[4];
      uint16_t pitch = (rxBuf[5] << 8) | rxBuf[6];
      uint16_t yaw   = (rxBuf[7] << 8) | rxBuf[8];
      uint16_t thr   = (rxBuf[9] << 8) | rxBuf[10];

      // Convert 11-bit RF to Betaflight RC us
      int rollUs  = rfToUs(roll);
      int pitchUs = rfToUs(pitch);
      int yawUs   = rfToUs(yaw);
      int thrUs   = rfToUs(thr);

      // Output RC to Betaflight
      sendCRSF_RC(rollUs, pitchUs, yawUs, thrUs);

      // Send telemetry back to transmitter
      sendRF_Telemetry();
    }

    radio.startReceive();
  }
}
