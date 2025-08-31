
# Plant Disease End-to-End Kit (Complete)

This package contains **everything** to run an end-to-end system:
- **FastAPI server** (image classification via TFLite or heuristic)
- **ESP32-CAM client** (uploads JPEG to `/predict`)
- **ESP32 nRF24 Sensor Node** (transmits environmental data)
- **ESP32 nRF24 Gateway** (receives and forwards to `/predict_values`)
- **Wiring & perfboard images** under `assets/`

## 0) Topology
```
[ESP32-CAM] --Wi-Fi--> [FastAPI Server] --> JSON result
[ESP32 Sensor Node + nRF24] --RF24--> [ESP32 Gateway] --HTTP--> [Server /predict_values]
```

## 1) Server Setup
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements-tflite-runtime.txt   # lightweight
# or: pip install -r requirements-tf.txt         # full CPU TF
uvicorn app.server:app --host 0.0.0.0 --port 8000
```
- If you have a TFLite model, place it at `app/model.tflite` and adjust `app/labels.txt`.
- Without a model, server runs a **green-ratio heuristic**.

## 2) ESP32-CAM (Image Uploader)
- Open `esp32cam_ai_client/esp32cam_ai_client.ino`
- Set `WIFI_SSID/WIFI_PASS/SERVER_IP`
- Board: **AI Thinker ESP32-CAM**
- Upload → Serial Monitor shows JSON results

## 3) ESP32 nRF24 Sensor Node
- Open `esp32_nrf24_sensor_node/esp32_nrf24_sensor_node.ino`
- Wiring (SPI/CE/CSN): see `assets/esp32_nrf24_wiring.png`
- Replace dummy sensor reads with your sensors (DHT, soil moisture, etc.)

## 4) ESP32 nRF24 Gateway (Receiver -> HTTP)
- Open `esp32_nrf24_gateway_http/esp32_nrf24_gateway_http.ino`
- Set `WIFI_SSID/WIFI_PASS/SERVER_URL`
- It receives RF24 packets, converts to JSON, and POSTs to `/predict_values`

## 5) Wiring & Perfboard
See `assets/esp32_nrf24_wiring.png` and `assets/perfboard_esp32_nrf24_layout.png`

**nRF24 power tip:** add 10–47 uF electrolytic cap across VCC-GND close to the module.

## 6) Test Flow
1. Start server: `uvicorn app.server:app --host 0.0.0.0 --port 8000`
2. Run ESP32-CAM → watch `/predict` JSON
3. Power Sensor Node + Gateway → watch `/predict_values` JSON on gateway serial
4. Check server logs; unhealthy images are saved to `app/alerts/`

## 7) Notes
- RF24 data rate options: 250KBPS (best range), 1MBPS (balanced), 2MBPS (fast, short range)
- Consider changing `radio.setChannel()` if interference occurs.
- For LINE/Telegram notifications, extend `app/server.py` after prediction.

Enjoy!
