import os
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from .feature_extractor import FeatureExtractor
except ImportError:  # Supports running this file directly during local development.
    from feature_extractor import FeatureExtractor

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

app = FastAPI(title="Phishing URL Classifier API", version="1.0.0")

model_path = MODEL_DIR / "phishing_rf_model.pkl"
features_path = MODEL_DIR / "feature_names.pkl"

if model_path.exists() and features_path.exists():
    model = joblib.load(model_path)
    feature_names = joblib.load(features_path)
else:
    model = None
    feature_names = [
        "url_length", "domain_length", "num_dots", "num_hyphens",
        "has_at_symbol", "has_ip", "domain_entropy",
    ]

extractor = FeatureExtractor()


class URLRequest(BaseModel):
    url: str


class ClassificationResponse(BaseModel):
    url: str
    score: float
    risk_level: str
    explanation: str


class ResponseGenerator:
    @staticmethod
    def get_risk_level(score: float) -> str:
        if score <= 1.0:
            return "SAFE"
        if score <= 3.0:
            return "SUSPICIOUS"
        return "PHISHING"

    @staticmethod
    def generate_explanation(features: Dict, risk_level: str) -> str:
        reasons = []
        if features.get("has_ip") == 1:
            reasons.append("uses a raw IP address instead of a domain name")
        if features.get("has_at_symbol") == 1:
            reasons.append("contains an '@' symbol")
        if features.get("num_hyphens", 0) >= 3:
            reasons.append("contains an unusually high number of hyphens")
        if features.get("domain_entropy", 0) > 3.5:
            reasons.append("has a highly random/complex domain name")
        if features.get("url_length", 0) > 80:
            reasons.append("is excessively long")
        if not reasons:
            return (
                "The URL structure appears standard and matches legitimate website patterns."
                if risk_level == "SAFE"
                else "The URL exhibits minor anomalies but lacks definitive malicious traits."
            )
        return f"This URL is classified as {risk_level.lower()} because it {', '.join(reasons)}."


response_gen = ResponseGenerator()


@app.post("/api/v1/check-url", response_model=ClassificationResponse)
async def check_url(request: URLRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model artifacts are not available.")
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL must not be empty.")
    try:
        raw_features = extractor.extract_features(request.url.strip())
        feature_vector = np.array([[raw_features.get(name, 0) for name in feature_names]])
        phishing_prob = float(model.predict_proba(feature_vector)[0][1])
        score = round(phishing_prob * 5.0, 1)
        risk_level = response_gen.get_risk_level(score)
        explanation = response_gen.generate_explanation(raw_features, risk_level)
        return ClassificationResponse(url=request.url, score=score, risk_level=risk_level, explanation=explanation)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification error: {exc}") from exc


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}


if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        if full_path.startswith(("api/", "health", "docs", "openapi.json")):
            raise HTTPException(status_code=404)
        requested = (FRONTEND_DIST / full_path).resolve()
        if requested.is_file() and FRONTEND_DIST in requested.parents:
            return FileResponse(requested)
        return FileResponse(FRONTEND_DIST / "index.html")
