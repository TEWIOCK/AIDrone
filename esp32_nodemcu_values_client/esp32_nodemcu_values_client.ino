// ESP32 NodeMCU -> FastAPI /predict_values (JSON)
// Example: send dummy sensor values every 5s
#include <WiFi.h>
#include <HTTPClient.h>

#define WIFI_SSID   "YOUR_WIFI_SSID"
#define WIFI_PASS   "YOUR_WIFI_PASSWORD"
#define SERVER_URL  "http://192.168.1.50:8000/predict_values" // change IP

void ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.printf("Connecting WiFi %s", WIFI_SSID);
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) {
    delay(300); Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK, IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi fail, retry later.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);
  ensureWiFi();
}

void loop() {
  ensureWiFi();
  if (WiFi.status() == WL_CONNECTED) {
    // TODO: replace with real sensor reads (e.g., DHT22, soil moisture)
    float temp = 25.0 + (float)(millis() % 1000) / 1000.0;   // dummy
    float humidity = 86.5;                                   // dummy
    float leaf_moisture = 0.72;                              // dummy

    String json = String("{\"device_id\":\"ESP32-NODEMCU-1\",\"values\":{") +
                  "\"temp\":" + String(temp, 2) + "," +
                  "\"humidity\":" + String(humidity, 1) + "," +
                  "\"leaf_moisture\":" + String(leaf_moisture, 2) + "}}";

    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(json);
    String resp = http.getString();
    http.end();

    Serial.printf("POST %s => %d\n", SERVER_URL, code);
    Serial.println(resp);
  }
  delay(5000);
}
