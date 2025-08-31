// ESP32 nRF24 Sensor Node (Transmitter)
// Sends sensor readings via nRF24 to a gateway
#include <SPI.h>
#include <RF24.h>

// Pins
#define CE_PIN   4
#define CSN_PIN  5

RF24 radio(CE_PIN, CSN_PIN);
const byte pipeAddr[6] = "GAT01"; // must match gateway's reading pipe

struct Payload {
  float temp;
  float humidity;
  float leaf_moisture;
  uint32_t seq;
};

uint32_t seq = 0;

void setup() {
  Serial.begin(115200);
  delay(200);
  if (!radio.begin()) {
    Serial.println("nRF24 init failed");
    while (1) delay(1000);
  }
  radio.setChannel(108);           // avoid crowded WiFi channels
  radio.setDataRate(RF24_1MBPS);   // balance range/throughput
  radio.setPALevel(RF24_PA_LOW);   // start low to reduce noise
  radio.openWritingPipe(pipeAddr);
  radio.stopListening();
  Serial.println("Sensor node ready");
}

void loop() {
  // TODO: replace with real sensor reads
  Payload p;
  p.temp = 25.0 + (millis()%1000)/200.0;
  p.humidity = 86.0;
  p.leaf_moisture = 0.72;
  p.seq = seq++;

  bool ok = radio.write(&p, sizeof(p));
  Serial.printf("TX seq=%lu => %s\n", (unsigned long)p.seq, ok ? "OK" : "FAIL");
  delay(1000);
}
