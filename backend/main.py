import os
import re
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from .feature_extractor import FeatureExtractor
except ImportError:
    from feature_extractor import FeatureExtractor

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
FEATURE_NAMES = [
    "url_length", "domain_length", "num_dots", "num_hyphens",
    "has_at_symbol", "has_ip", "domain_entropy",
]

app = FastAPI(title="Phishing URL Classifier API", version="1.0.0")
extractor = FeatureExtractor()
model = None
feature_names = FEATURE_NAMES
model_error = None

# Model files are optional at startup. A malformed or incompatible pickle must
# not prevent Render from starting the health endpoint.
model_path = MODEL_DIR / "phishing_rf_model.pkl"
features_path = MODEL_DIR / "feature_names.pkl"
if model_path.exists() and features_path.exists():
    try:
        model = joblib.load(model_path)
        loaded_names = joblib.load(features_path)
        if isinstance(loaded_names, (list, tuple)) and loaded_names:
            feature_names = list(loaded_names)
    except Exception as exc:
        model_error = f"Model could not be loaded: {exc}"
        model = None


class URLRequest(BaseModel):
    url: str


class ClassificationResponse(BaseModel):
    url: str
    score: float
    risk_level: str
    explanation: str


def risk_level(score: float) -> str:
    if score <= 1.0:
        return "SAFE"
    if score <= 3.0:
        return "SUSPICIOUS"
    return "PHISHING"


def heuristic_score(features: Dict) -> float:
    # Safe fallback used only when the optional model artifact is unavailable.
    score = 0.0
    score += 2.0 if features.get("has_ip") else 0.0
    score += 1.5 if features.get("has_at_symbol") else 0.0
    score += min(float(features.get("num_hyphens", 0)) * 0.35, 1.5)
    score += 1.0 if features.get("domain_entropy", 0) > 3.5 else 0.0
    score += 1.0 if features.get("url_length", 0) > 80 else 0.0
    return round(min(score, 5.0), 1)


def explanation(features: Dict, level: str) -> str:
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
        return "The URL structure appears standard and matches legitimate website patterns."
    return f"This URL is classified as {level.lower()} because it {', '.join(reasons)}."


@app.post("/api/v1/check-url", response_model=ClassificationResponse)
async def check_url(request: URLRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL must not be empty.")

    features = extractor.extract_features(url)
    try:
        if model is not None:
            vector = np.array([[features.get(name, 0) for name in feature_names]])
            probability = float(model.predict_proba(vector)[0][1])
            score = round(probability * 5.0, 1)
        else:
            score = heuristic_score(features)
        level = risk_level(score)
        return ClassificationResponse(url=url, score=score, risk_level=level, explanation=explanation(features, level))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification error: {exc}") from exc


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_fallback": model is None,
        "model_error": model_error,
    }


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
