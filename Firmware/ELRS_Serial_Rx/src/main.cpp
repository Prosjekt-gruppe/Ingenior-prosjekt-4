#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

WebServer server(80);
String lastValue = "No data yet";

void handleRoot() {
  String html = "<html><head><meta http-equiv='refresh' content='1'></head><body>";
  html += "<h1>ESP32 Serial Data</h1>";
  html += "<p>Latest value: <b>" + lastValue + "</b></p>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected! IP: ");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.begin();
}

void loop() {
  server.handleClient();

  if (Serial.available()) {
    lastValue = Serial.readStringUntil('\n');
    lastValue.trim();
    Serial.println("Received from Python: " + lastValue);
  }
}
