#include <Arduino.h>

void setup() {
  Serial.begin(115200);      // USB serial
  Serial1.begin(115200, SERIAL_8N1, 16, 17);  // Use pins 16=RX, 17=TX
}

void loop() {
  if (Serial.available()) Serial1.write(Serial.read());
  if (Serial1.available()) Serial.write(Serial1.read());
}
