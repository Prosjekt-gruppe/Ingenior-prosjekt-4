#include <Arduino.h>
#include <RadioLib.h>
#include <ArduinoJson.h>

// ----------- SX1280 / Lambda80 wiring ----------
static const int SX_CS   = 5;
static const int SX_DIO1 = 26;
static const int SX_RST  = 25;
static const int SX_BUSY = 27;

SX1280 radio = new Module(SX_CS, SX_DIO1, SX_RST, SX_BUSY);

// ----------- link packets ----------
static const uint8_t CTRL_SYNC  = 0xA5;
static const uint8_t TELE_SYNC  = 0x5A;
static const size_t  CTRL_LEN   = 12;
static const size_t  TELE_LEN   = 8;

// last known RC values (µs)
volatile int g_rollUs  = 1500;
volatile int g_pitchUs = 1500;
volatile int g_yawUs   = 1500;
volatile int g_thrUs   = 1000;

uint8_t frameCounter = 0;

// --- CRC-8 for link packets (poly 0x8C) ---
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

// map us -> 11-bit 0..2047 for RF packet
uint16_t mapUsTo11bit(int us) {
  if (us < 1000) us = 1000;
  if (us > 2000) us = 2000;
  return (uint16_t)((us - 1000) * 2047L / 1000L);
}

// --- parse JSON RC from Serial (line-based) ---
void processSerialJsonLine(const String& line) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) {
    Serial.print("JSON error: "); Serial.println(err.f_str());
    return;
  }

  // optional "type" field
  const char* type = doc["type"] | "rc";
  if (strcmp(type, "rc") != 0) {
    return;
  }

  if (doc.containsKey("roll"))     g_rollUs  = doc["roll"];
  if (doc.containsKey("pitch"))    g_pitchUs = doc["pitch"];
  if (doc.containsKey("yaw"))      g_yawUs   = doc["yaw"];
  if (doc.containsKey("throttle")) g_thrUs   = doc["throttle"];
}

// --- read Serial non-blocking, split by '\n' ---
void pollSerialJson() {
  static String buf;
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      if (buf.length() > 0) {
        processSerialJsonLine(buf);
        buf = "";
      }
    } else {
      if (buf.length() < 240) {
        buf += c;
      } else {
        // overflow - reset
        buf = "";
      }
    }
  }
}

// --- build and send one control packet ---
void sendControlFrame() {
  uint8_t txBuf[CTRL_LEN];

  uint16_t c1 = mapUsTo11bit(g_rollUs);
  uint16_t c2 = mapUsTo11bit(g_pitchUs);
  uint16_t c3 = mapUsTo11bit(g_yawUs);
  uint16_t c4 = mapUsTo11bit(g_thrUs);

  txBuf[0]  = CTRL_SYNC;
  txBuf[1]  = frameCounter++;
  txBuf[2]  = 0x00;   // flags placeholder

  txBuf[3]  = (c1 >> 8) & 0xFF;
  txBuf[4]  =  c1       & 0xFF;
  txBuf[5]  = (c2 >> 8) & 0xFF;
  txBuf[6]  =  c2       & 0xFF;
  txBuf[7]  = (c3 >> 8) & 0xFF;
  txBuf[8]  =  c3       & 0xFF;
  txBuf[9]  = (c4 >> 8) & 0xFF;
  txBuf[10] =  c4       & 0xFF;

  txBuf[11] = linkCrc8(txBuf, 11);

  int16_t st = radio.transmit(txBuf, CTRL_LEN);
  if (st != RADIOLIB_ERR_NONE) {
    Serial.print("TX err "); Serial.println(st);
  }
}

// --- wait short window for telemetry, print JSON if received ---
void receiveTelemetryWindow() {
  radio.startReceive();
  unsigned long start = micros();
  const unsigned long windowUs = 3000; // ~3 ms

  while ((micros() - start) < windowUs) {
    uint8_t buf[TELE_LEN];
    int16_t st = radio.readData(buf, sizeof(buf));
    if (st == RADIOLIB_ERR_NONE) {
      size_t len = radio.getPacketLength();
      if (len == TELE_LEN && buf[0] == TELE_SYNC && linkCrc8(buf, 7) == buf[7]) {
        uint16_t batt = (buf[1] << 8) | buf[2];
        int8_t   rssi = (int8_t)buf[3];
        uint8_t  lq   = buf[4];

        // output telemetry JSON
        StaticJsonDocument<256> doc;
        doc["type"]    = "telemetry";
        doc["batt_mv"] = batt;
        doc["rssi"]    = rssi;
        doc["lq"]      = lq;

        String out;
        serializeJson(doc, out);
        Serial.println(out);
      }
      break; // done for this frame
      } else if (st != RADIOLIB_ERR_RX_TIMEOUT && st != RADIOLIB_ERR_WRONG_MODEM) {

      // some other error - ignore and break
      break;
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("TX: boot");

  SPI.begin(18, 19, 23);
  int16_t state = radio.beginFLRC(
    2440.0,     // MHz
    1300,       // kbps
    1,          // coding rate idx
    10,         // dBm
    16,         // preamble
    RADIOLIB_SHAPING_0_5
  );
  if (state != RADIOLIB_ERR_NONE) {
    Serial.print("Radio init failed, code "); Serial.println(state);
    while (true) delay(100);
  }
}

void loop() {
  // 1) Update RC from JSON UART if new data available
  pollSerialJson();

  // 2) Send control frame
  sendControlFrame();

  // 3) Telemetry window (drone replies right after its RX)
  receiveTelemetryWindow();

  // 4) Repeat at ~250 Hz
  delay(4);
}
