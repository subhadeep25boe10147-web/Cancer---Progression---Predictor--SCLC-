"""Local web server that exposes the project's trained SCLC model with Live ECG & Stretch Streaming."""

# 1. Compiler directives MUST be the absolute first line
from __future__ import annotations

# 2. Eventlet monkey patching MUST happen before ANY other standard imports
import eventlet
eventlet.monkey_patch()

# 3. Now it is safe to load the rest of the libraries
import json
import os
from datetime import datetime
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

inference_buffer = deque(maxlen=300)
stretch_buffer = deque(maxlen=300)
current_patient_state = {"baseline_score": 50.0} 

def calculate_dynamic_csp(baseline_score: float, heart_rate: float) -> float:
    if heart_rate > 100:
        stress_modifier = 1.25 
    elif heart_rate > 85:
        stress_modifier = 1.12
    elif heart_rate < 55:
        stress_modifier = 1.15
    else:
        stress_modifier = 1.00
    return round(min(max(baseline_score * stress_modifier, 0.0), 100.0), 2)

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_assets(path):
    allowed_assets = [
        "index.html", "styles.css", "app.js", 
        "assets/oncomech-ai-logo.png", "assets/logo-website.jpeg"
    ]
    if path in allowed_assets:
        return app.send_static_file(path)
    return jsonify({"error": "Asset not found"}), 404

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        inputs = request.get_json()
        patient_id = inputs.get("Patient_ID", "Unknown_PT")
        
        patient_data = {name: float(inputs.get(name, 0)) for name in FEATURES}
        patient = pd.DataFrame([patient_data], columns=FEATURES)
        
        if MODEL:
            baseline = float(MODEL.predict(patient)[0])
        else:
            baseline = 50.0
            
        current_patient_state["baseline_score"] = baseline
        
        # --- NEW: BACKEND DATA LOGGING ---
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_id": patient_id,
            "clinical_inputs": patient_data,
            "baseline_score": baseline
        }
        
        records_file = ROOT / "records.json"
        with open(records_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        # ---------------------------------
        
        return jsonify({"score": baseline}), 200
        
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": f"Invalid model inputs: {error}"}), 400
    except Exception as error:
        return jsonify({"error": f"Prediction failed: {error}"}), 500

@socketio.on('sensor_data')
def handle_live_stream(data):
    try:
        ecg_val = float(data.get('ecg_value', 0))
        stretch_val = float(data.get('stretch_value', 0))
        
        inference_buffer.append(ecg_val)
        stretch_buffer.append(stretch_val)

        emit('signal_feed', {'ecg_val': ecg_val, 'stretch_val': stretch_val}, broadcast=True)

        if len(inference_buffer) == 300:
            ecg_array = np.array(inference_buffer)
            ecg_peaks, _ = find_peaks(ecg_array, distance=40, height=np.mean(ecg_array))
            bpm = (len(ecg_peaks) / 5.0) * 60
            updated_score = calculate_dynamic_csp(current_patient_state["baseline_score"], bpm)
            emit('score_feed', {'score': updated_score}, broadcast=True)

            stretch_array = np.array(stretch_buffer)
            stretch_amplitude = np.max(stretch_array) - np.min(stretch_array)
            stretch_peaks, _ = find_peaks(stretch_array, distance=60)
            stretch_hz = len(stretch_peaks) / 5.0
            
            emit('biomechanics_update', {
                'amplitude': round(stretch_amplitude, 1),
                'frequency': round(stretch_hz, 2),
                'bpm': int(bpm)
            }, broadcast=True)

    except Exception as e:
        emit('server_error', {'message': str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"OncoMech AI Streaming Server is running at http://0.0.0.0:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
