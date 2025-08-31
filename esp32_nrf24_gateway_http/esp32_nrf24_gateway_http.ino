// ESP32 nRF24 Gateway (Receiver) -> HTTP POST to FastAPI /predict_values
#include <SPI.h>
#include <RF24.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ---- WiFi / Server ----
#define WIFI_SSID   "YOUR_WIFI_SSID"
#define WIFI_PASS   "YOUR_WIFI_PASSWORD"
#define SERVER_URL  "http://192.168.1.50:8000/predict_values" // change to your server

// ---- nRF24 Pins ----
#define CE_PIN   4
#define CSN_PIN  5

RF24 radio(CE_PIN, CSN_PIN);
const byte pipeAddr[6] = "GAT01"; // must match sensor node

struct Payload {
  float temp;
  float humidity;
  float leaf_moisture;
  uint32_t seq;
};

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

  if (!radio.begin()) {
    Serial.println("nRF24 init failed");
    while (1) delay(1000);
  }
  radio.setChannel(108);
  radio.setDataRate(RF24_1MBPS);
  radio.setPALevel(RF24_PA_LOW);
  radio.openReadingPipe(1, pipeAddr);
  radio.startListening();
  Serial.println("Gateway ready");
}

void loop() {
  ensureWiFi();

  if (radio.available()) {
    Payload p;
    while (radio.available()) {
      radio.read(&p, sizeof(p));
    }

    // Build JSON
    String json = String("{\"device_id\":\"ESP32-GATEWAY\",\"values\":{") +
                  "\"temp\":" + String(p.temp, 2) + "," +
                  "\"humidity\":" + String(p.humidity, 1) + "," +
                  "\"leaf_moisture\":" + String(p.leaf_moisture, 2) + "}}";

    // POST to server
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(SERVER_URL);
      http.addHeader("Content-Type", "application/json");
      int code = http.POST(json);
      String resp = http.getString();
      http.end();

      Serial.printf("POST %s => %d\n", SERVER_URL, code);
      Serial.println(resp);
    } else {
      Serial.println("WiFi not connected");
    }

    Serial.printf("RX seq=%lu\n", (unsigned long)p.seq);
  }
}
