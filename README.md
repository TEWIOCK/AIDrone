# Plant Disease Inference — Full Server + ESP32 Clients

This package gives you:
- **FastAPI server** (`app/server.py`) with two modes:
  - **TFLite mode** (if `model.tflite` exists in `app/`): real image classification
  - **Heuristic mode** (no model required): a simple green-ratio check
- **ESP32 example clients**:
  - `esp32cam_ai_client/esp32cam_ai_client.ino`: capture JPEG and POST `/predict`
  - `esp32_nodemcu_values_client/esp32_nodemcu_values_client.ino`: send JSON to `/predict_values`

## 1) Server Setup

### Option A: TensorFlow Lite (full TF CPU)
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements-tf.txt
```
Place your `model.tflite` and `labels.txt` into `app/` (a sample `labels.txt` is provided).

### Option B: Lightweight TFLite Runtime (recommended on small CPUs)
```bash
python -m venv venv
# activate as above...
pip install -r requirements-tflite-runtime.txt
```
Then copy your TFLite model to `app/model.tflite`.

### Run
```bash
uvicorn app.server:app --host 0.0.0.0 --port 8000
```
- API docs: `http://<SERVER_IP>:8000/docs`
- If `model.tflite` is missing, server falls back to heuristic mode.
- Unhealthy predictions save the original image to `app/alerts/` with metadata.

## 2) ESP32 Clients

### A) ESP32-CAM (AI Thinker pinout)
- Open `esp32cam_ai_client/esp32cam_ai_client.ino` in Arduino IDE
- Install **ESP32 board support** in Boards Manager
- Select *AI Thinker ESP32-CAM*
- Set your Wi‑Fi SSID/PASS and `SERVER_IP`
- Upload (GPIO0 -> GND to flash), then reset.
- Serial Monitor will show JSON results returned from server.

### B) ESP32 NodeMCU (WROOM/WROVER, no camera)
- Open `esp32_nodemcu_values_client/esp32_nodemcu_values_client.ino`
- This sends JSON sensor values (e.g., DHT temp/humidity) to `/predict_values`.
- Adjust to your sensors. If you need image inference, you must attach a camera
  module and implement capture via ESP32 I2S camera driver, or use an ESP32‑CAM.

## 3) Notes
- For real plant disease classification, train/obtain a `model.tflite` with matching `labels.txt`.
- Match preprocessing in `app/server.py` (`preprocess_img_tflite`) to your training pipeline.
- For LINE/Telegram alerts, extend server after the prediction step.

Good luck & have fun!
