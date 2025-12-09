#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

WebServer server(80);

String incoming = "";
String lastControl = "No control data yet";
unsigned long lastTelemetry = 0;

void handleRoot() {
  String html = "<html><head><meta http-equiv='refresh' content='1'></head><body>";
  html += "<h1>ESP32 Drone Telemetry Server</h1>";
  html += "<p><b>Last Control Input:</b> " + lastControl + "</p>";
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
  Serial.print("Connected! IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.begin();
}

void loop() {
  server.handleClient();

  // ---- RECEIVE CONTROL INPUTS ----
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      incoming.trim();
      lastControl = incoming;
      Serial.print("Received control: ");
      Serial.println(incoming);
      incoming = "";
    } else {
      incoming += c;
    }
  }

  // ---- SEND TELEMETRY ----
  if (millis() - lastTelemetry > 100) { // every 100 ms
    lastTelemetry = millis();
    float altitude = random(100, 200) / 1.0;
    float speed = random(0, 50) / 1.0;
    float battery = random(70, 100) / 1.0;

    String telemetry = "ALT:" + String(altitude) + ",SPD:" + String(speed) + ",BAT:" + String(battery);
    Serial.println(telemetry);
  }
}
