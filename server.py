"""Local web server that exposes the project's trained SCLC model to the browser."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "dist" / "model.pkl"
FEATURES = [
    "Age", "Sex", "Smoking", "Smoking_PackYears", "Stretch", "Frequency",
    "Stretch_Duration", "Fibrosis", "Tissue_Stiffness", "IL6", "VEGF", "Ki67", "Tumor_Size",
]

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "No trained model found. Run '.\\.venv\\Scripts\\python.exe train_model.py' first."
    )

MODEL = joblib.load(MODEL_PATH)


class AppHandler(SimpleHTTPRequestHandler):
    """Serve static assets and make the original Random Forest available at /api/predict."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):  # noqa: N802 - stdlib HTTP hook
        """Expose only the browser assets; never publish the dataset or model file."""
        assets = {
            "/": "/index.html",
            "/index.html": "/index.html",
            "/styles.css": "/styles.css",
            "/app.js": "/app.js",
        }
        if self.path not in assets:
            self.send_error(HTTPStatus.NOT_FOUND, "Asset not found")
            return
        self.path = assets[self.path]
        super().do_GET()

    def do_POST(self):  # noqa: N802 - stdlib HTTP hook
        if self.path != "/api/predict":
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            inputs = json.loads(self.rfile.read(length))
            patient = pd.DataFrame([{name: float(inputs[name]) for name in FEATURES}], columns=FEATURES)
            score = float(MODEL.predict(patient)[0])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid model inputs: {error}"})
            return
        except Exception as error:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Prediction failed: {error}"})
            return
        self._send_json(HTTPStatus.OK, {"score": score})

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"OncoMech AI is running at http://127.0.0.1:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), AppHandler).serve_forever()
