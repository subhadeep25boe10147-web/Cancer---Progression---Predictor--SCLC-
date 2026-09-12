"""Local web server that exposes the project's trained SCLC model with Live ECG Streaming."""

from __future__ import annotations

# CRITICAL: Monkey patching must happen before other imports for async websockets to work
import eventlet
eventlet.monkey_patch()

import json
import os
from pathlib import Path
from collections import deque

import joblib
import pandas as pd
import numpy as np
from scipy.signal import find_peaks

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "dist" / "model.pkl"

# We keep your exact 13 features! No model retraining required.
FEATURES = [
    "Age", "Sex", "Smoking", "Smoking_PackYears", "Stretch", "Frequency",
    "Stretch_Duration", "Fibrosis", "Tissue_Stiffness", "IL6", "VEGF", "Ki67", "Tumor_Size",
]

app = Flask(__name__, static_folder=str(ROOT), static_url_path='')
app.config['SECRET_KEY'] = 'oncomech_secure_key'

# Initialize SocketIO for real-time sensor streams
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

if not MODEL_PATH.exists():
    print("WARNING: No trained model found. Run '.\\.venv\\Scripts\\python.exe train_model.py' first.")
    MODEL = None
else:
    MODEL = joblib.load(MODEL_PATH)

# Buffers and session state for the dynamic score modulator
inference_buffer = deque(maxlen=300)
current_patient_state = {"baseline_score": 50.0}  # Default fallback score

def calculate_dynamic_csp(baseline_score: float, heart_rate: float) -> float:
    """Adjusts baseline progression score based on cardiac physiological strain."""
    if heart_rate > 100:
        stress_modifier = 1.25  # High tachycardia
    elif heart_rate > 85:
        stress_modifier = 1.12  # Mild autonomic elevation
    elif heart_rate < 55:
        stress_modifier = 1.15  # Severe bradycardia
    else:
        stress_modifier = 1.00  # Stable resting range

    adjusted_score = baseline_score * stress_modifier
    return round(min(max(adjusted_score, 0.0), 100.0), 2)

# ==========================================
# 1. STATIC ASSET ROUTING
# ==========================================
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_assets(path):
    # Your exact whitelist of allowed files
    allowed_assets = [
        "index.html", "styles.css", "app.js", 
        "assets/oncomech-ai-logo.png", "assets/logo-website.jpeg"
    ]
    if path in allowed_assets:
        return app.send_static_file(path)
    return jsonify({"error": "Asset not found"}), 404

# ==========================================
# 2. MACHINE LEARNING PREDICTION ROUTE
# ==========================================
@app.route('/api/predict', methods=['POST'])
def predict():
    """Calculates baseline score from static clinical inputs and stores it for live updates."""
    try:
        inputs = request.get_json()
        
        # Build dataframe using only the 13 features expected by the model
        patient_data = {name: float(inputs.get(name, 0)) for name in FEATURES}
        patient = pd.DataFrame([patient_data], columns=FEATURES)
        
        if MODEL:
            baseline = float(MODEL.predict(patient)[0])
        else:
            baseline = 50.0
            
        # Store this baseline so the live ECG stream can modify it
        current_patient_state["baseline_score"] = baseline
        
        return jsonify({"score": baseline}), 200
        
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": f"Invalid model inputs: {error}"}), 400
    except Exception as error:
        return jsonify({"error": f"Prediction failed: {error}"}), 500

# ==========================================
# 3. LIVE ECG WEBSOCKET ROUTE
# ==========================================
@socketio.on('ecg_data')
def handle_live_stream(data):
    """Processes incoming sensor packets and silently recalculates the progression score."""
    try:
        ecg_val = float(data.get('value', 0))
        inference_buffer.append(ecg_val)

        # Broadcast raw signal point for the visual oscilloscope
        emit('signal_feed', {'val': ecg_val}, broadcast=True)

        # Calculate heart rate and update the score in the background
        if len(inference_buffer) == 300:
            signal_array = np.array(inference_buffer)
            peaks, _ = find_peaks(signal_array, distance=40, height=np.mean(signal_array))

            # 300 samples at ~60Hz = 5 second window -> (peaks / 5) * 60 = BPM
            bpm = (len(peaks) / 5.0) * 60

            # Calculate the updated score silently in the backend
            updated_score = calculate_dynamic_csp(current_patient_state["baseline_score"], bpm)

            # Emit ONLY the updated score to the user dashboard
            emit('score_feed', {'score': updated_score}, broadcast=True)

    except Exception as e:
        emit('server_error', {'message': str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"OncoMech AI Streaming Server is running at http://127.0.0.1:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
