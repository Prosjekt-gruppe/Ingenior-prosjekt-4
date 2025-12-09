#include <Arduino.h>

void setup() {
    // Initialize serial communication at 9600 bits per second
    Serial.begin(9600);
}

void loop() {
  int sensorValue = random(0, 1024); // Simulate reading from a sensor
  Serial.print("Sensor Value: ");
  Serial.println(sensorValue);
  delay(1000); // Wait for 1 second before the next loop
}