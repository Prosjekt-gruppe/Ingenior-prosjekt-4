#include <Arduino.h>
#include <RadioLib.h>
#include <ArduinoJson.h>

/* ============================================================
   Hardware Configuration
   ============================================================ */

// SX1280 / Lambda80 wiring
static const int PIN_CS   = 5;
static const int PIN_DIO1 = 26;
static const int PIN_RST  = 25;
static const int PIN_BUSY = 27;

// Create RadioLib module object
SX1280 radio = new Module(PIN_CS, PIN_DIO1, PIN_RST, PIN_BUSY);

/* ============================================================
   Protocol Constants
   ============================================================ */

const uint8_t SYNC_CONTROL   = 0xA5;
const uint8_t SYNC_TELEMETRY = 0x5A;

const size_t CONTROL_LEN   = 12;
const size_t TELEMETRY_LEN = 8;

/* ============================================================
   RC Input State
   ============================================================ */

volatile int rollUs     = 1500;
volatile int pitchUs    = 1500;
volatile int yawUs      = 1500;
volatile int throttleUs = 1000;

uint8_t frameCounter = 0;

/* ============================================================
   Utility Functions
   ============================================================ */

// --- CRC for control/telemetry (poly 0x8C) ---
uint8_t crcRF(const uint8_t* data, uint8_t len) {
  uint8_t crc = 0;
  while (len--) {
    uint8_t in = *data++;
    for (uint8_t i = 0; i < 8; i++) {
      uint8_t mix = (crc ^ in) & 1;
      crc >>= 1;
      if (mix) crc ^= 0x8C;
      in >>= 1;
    }
  }
  return crc;
}

// Convert RC microseconds → 11-bit 0..2047 for RF
uint16_t usTo11bit(int us) {
  us = constrain(us, 1000, 2000);
  return (uint16_t)((us - 1000) * 2047L / 1000L);
}

/* ============================================================
   JSON Input Handling
   ============================================================ */

void handleJsonLine(const String& line) {
  StaticJsonDocument<256> doc;

  auto err = deserializeJson(doc, line);
  if (err) {
    Serial.print("JSON error: ");
    Serial.println(err.f_str());
    return;
  }

  // Optional "type": "rc"
  const char* type = doc["type"] | "rc";
  if (strcmp(type, "rc") != 0) return;

  if (doc.containsKey("roll"))     rollUs     = doc["roll"];
  if (doc.containsKey("pitch"))    pitchUs    = doc["pitch"];
  if (doc.containsKey("yaw"))      yawUs      = doc["yaw"];
  if (doc.containsKey("throttle")) throttleUs = doc["throttle"];
}

// Read Serial line-by-line, non-blocking
void pollJsonInput() {
  static String buffer;

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\r') continue;

    if (c == '\n') {
      if (buffer.length() > 0) {
        handleJsonLine(buffer);
        buffer = "";
      }
      continue;
    }

    // accumulate
    if (buffer.length() < 240) {
      buffer += c;
    } else {
      buffer = "";  // overflow: reset buffer
    }
  }
}

/* ============================================================
   RF: Send Control Frames
   ============================================================ */

void sendControlPacket() {
  uint8_t tx[CONTROL_LEN];

  // Convert RC → 11-bit values
  uint16_t c1 = usTo11bit(rollUs);
  uint16_t c2 = usTo11bit(pitchUs);
  uint16_t c3 = usTo11bit(yawUs);
  uint16_t c4 = usTo11bit(throttleUs);

  tx[0]  = SYNC_CONTROL;
  tx[1]  = frameCounter++;
  tx[2]  = 0x00;   // reserved flags

  tx[3]  = c1 >> 8;
  tx[4]  = c1 & 0xFF;
  tx[5]  = c2 >> 8;
  tx[6]  = c2 & 0xFF;
  tx[7]  = c3 >> 8;
  tx[8]  = c3 & 0xFF;
  tx[9]  = c4 >> 8;
  tx[10] = c4 & 0xFF;

  tx[11] = crcRF(tx, 11);

  int16_t st = radio.transmit(tx, CONTROL_LEN);
  if (st != RADIOLIB_ERR_NONE) {
    Serial.print("TX error: ");
    Serial.println(st);
  }
}

/* ============================================================
   RF: Receive Telemetry Frames
   ============================================================ */

void receiveTelemetry() {
  // Switch to RX mode
  radio.startReceive();

  const unsigned long windowUs = 3000;    // ~3 ms
  unsigned long start = micros();

  while (micros() - start < windowUs) {
    uint8_t buf[TELEMETRY_LEN];
    int16_t st = radio.readData(buf, sizeof(buf));

    if (st == RADIOLIB_ERR_NONE) {
      size_t len = radio.getPacketLength();

      bool ok =
        (len == TELEMETRY_LEN) &&
        (buf[0] == SYNC_TELEMETRY) &&
        (crcRF(buf, 7) == buf[7]);

      if (ok) {
        uint16_t batt = (buf[1] << 8) | buf[2];
        int8_t   rssi = buf[3];
        uint8_t  lq   = buf[4];

        // Output telemetry JSON
        StaticJsonDocument<256> doc;
        doc["type"]    = "telemetry";
        doc["batt_mv"] = batt;
        doc["rssi"]    = rssi;
        doc["lq"]      = lq;

        String out;
        serializeJson(doc, out);
        Serial.println(out);
      }
      break;  // whether good or bad packet, exit window
    }

    else if (st != RADIOLIB_ERR_RX_TIMEOUT &&
             st != RADIOLIB_ERR_WRONG_MODEM) {
      // Unexpected error — ignore and exit
      break;
    }
  }
}

/* ============================================================
   Setup
   ============================================================ */

void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.println("TX: Starting...");

  // SPI for SX1280
  SPI.begin(18, 19, 23);

  int16_t err = radio.beginFLRC(
    2440.0,     // MHz
    1300,       // kbps
    1,          // coding rate index
    10,         // dBm output power
    16,         // preamble length
    RADIOLIB_SHAPING_0_5
  );

  if (err != RADIOLIB_ERR_NONE) {
    Serial.print("Radio init failed: ");
    Serial.println(err);
    while (true) delay(100);
  }
}

/* ============================================================
   Main Loop
   ============================================================ */

void loop() {

  // 1) Update RC input from JSON
  pollJsonInput();

  // 2) Send control frame to quad
  sendControlPacket();

  // 3) Listen briefly for telemetry reply
  receiveTelemetry();

  // 4) Maintain ~250 Hz loop
  delay(4);
}
