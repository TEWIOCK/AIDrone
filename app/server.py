# Plant Disease Inference API (FastAPI)
# - If "model.tflite" exists, use TFLite classification
# - Else fallback to a simple green-ratio heuristic as a demo
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import numpy as np
import io, os, time, datetime

APP_TITLE = "Plant Disease Inference API"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.tflite")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "labels.txt")

app = FastAPI(title=APP_TITLE)

# CORS (allow local testing from anywhere)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------- Optional TFLite backend --------
USE_TFLITE = os.path.exists(MODEL_PATH)
INTERPRETER = None
INPUT_DETAILS = None
OUTPUT_DETAILS = None
LABELS = []

if USE_TFLITE:
    try:
        from tensorflow.lite.python.interpreter import Interpreter  # uses tensorflow-cpu
    except Exception:
        from tflite_runtime.interpreter import Interpreter  # fallback
    INTERPRETER = Interpreter(model_path=MODEL_PATH)
    INTERPRETER.allocate_tensors()
    INPUT_DETAILS = INTERPRETER.get_input_details()
    OUTPUT_DETAILS = INTERPRETER.get_output_details()
    # load labels if present
    if os.path.exists(LABELS_PATH):
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            LABELS = [ln.strip() for ln in f if ln.strip()]
    else:
        # assume N classes from model output shape if labels missing
        n = OUTPUT_DETAILS[0]['shape'][-1] if OUTPUT_DETAILS else 2
        LABELS = [f"class_{i}" for i in range(n)]

# ------- Utils --------
def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)
    return p

ALERT_DIR = ensure_dir(os.path.join(os.path.dirname(__file__), "alerts"))

def preprocess_img_tflite(img: Image.Image):
    in_h = INPUT_DETAILS[0]['shape'][1]
    in_w = INPUT_DETAILS[0]['shape'][2]
    x = img.convert("RGB").resize((in_w, in_h))
    arr = np.array(x, dtype=np.float32) / 255.0
    # NOTE: adjust if your model uses different scaling (e.g., [-1,1])
    # arr = (arr - 0.5) * 2.0
    return np.expand_dims(arr, axis=0)

def infer_tflite(arr: np.ndarray):
    INTERPRETER.set_tensor(INPUT_DETAILS[0]['index'], arr)
    INTERPRETER.invoke()
    preds = INTERPRETER.get_tensor(OUTPUT_DETAILS[0]['index'])[0]
    idx = int(np.argmax(preds))
    score = float(preds[idx])
    label = LABELS[idx] if idx < len(LABELS) else f"class_{idx}"
    healthy = ("healthy" in label.lower()) or ("normal" in label.lower())
    return label, score, healthy

def green_ratio_heuristic(img: Image.Image):
    # Downscale for speed
    small = img.convert("RGB").resize((128, 128))
    arr = np.asarray(small).astype(np.float32)
    r, g, b = arr[...,0], arr[...,1], arr[...,2]
    eps = 1e-6
    green_ratio = np.mean(g / (r + b + eps))
    # Heuristic threshold: tweakable
    healthy = green_ratio >= 0.6
    label = "healthy (heuristic)" if healthy else "possibly_diseased (heuristic)"
    score = float(min(0.99, max(0.01, (green_ratio - 0.4) / 0.5)))  # normalize ~[0,1]
    return label, score, healthy, green_ratio

def save_alert_image(img_bytes: bytes, meta: dict):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    fname = f"alert_{ts}.jpg"
    with open(os.path.join(ALERT_DIR, fname), "wb") as f:
        f.write(img_bytes)
    with open(os.path.join(ALERT_DIR, fname + ".json"), "w", encoding="utf-8") as f:
        import json
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return fname

# ------- Schemas --------
class SensorPacket(BaseModel):
    device_id: str
    values: dict

# ------- Routes --------
@app.get("/")
def root():
    mode = "tflite" if USE_TFLITE else "heuristic"
    return {"ok": True, "mode": mode, "message": "Plant Disease API is running."}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Image endpoint (ESP32-CAM or any client can POST JPEG)."""
    t0 = time.time()
    raw = await file.read()
    try:
        img = Image.open(io.BytesIO(raw))
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid image"})

    if USE_TFLITE:
        arr = preprocess_img_tflite(img)
        label, score, healthy = infer_tflite(arr)
        extra = {}
    else:
        label, score, healthy, green_ratio = green_ratio_heuristic(img)
        extra = {"green_ratio": round(green_ratio, 4)}

    latency = round((time.time() - t0) * 1000, 1)
    result = {
        "label": label,
        "score": round(score, 4),
        "healthy": bool(healthy),
        "latency_ms": latency,
        "w": img.width, "h": img.height,
        **extra
    }

    # save alerts if unhealthy
    if not healthy:
        fname = save_alert_image(raw, {"result": result})
        result["saved_alert"] = fname

    return result

@app.post("/predict_values")
def predict_values(pkt: SensorPacket):
    """Optional endpoint for non-image ESP32 boards posting sensor values (JSON)."""
    # Simple rule demo: you should replace with a real model if needed.
    # Example expects keys like "temp", "humidity", "leaf_moisture", etc.
    v = pkt.values
    risk = 0.0
    if "humidity" in v:
        h = float(v["humidity"])
        risk += 0.4 if h > 85 else 0.1
    if "temp" in v:
        t = float(v["temp"])
        risk += 0.3 if (18 <= t <= 26) else 0.1
    if "leaf_moisture" in v:
        m = float(v["leaf_moisture"])
        risk += 0.4 if m > 0.7 else 0.1

    risk = min(1.0, max(0.0, risk))
    healthy = risk < 0.5
    return {
        "device_id": pkt.device_id,
        "healthy": healthy,
        "disease_risk": round(risk, 3),
        "advice": "Increase airflow and monitor leaves" if not healthy else "Looks fine",
    }
