# backend/main.py
import os
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict

# Import local modules
from feature_extractor import FeatureExtractor

app = FastAPI(title="Phishing URL Classifier API", version="1.0.0")

# Load Model and Extractor at startup
model_path = './models/phishing_rf_model.pkl'
features_path = './models/feature_names.pkl'

# Fallback if models aren't pre-built (for initial deployment)
if os.path.exists(model_path):
    model = joblib.load(model_path)
    feature_names = joblib.load(features_path)
else:
    model = None
    feature_names = ['url_length', 'domain_length', 'num_dots', 'num_hyphens', 'has_at_symbol', 'has_ip', 'domain_entropy']

extractor = FeatureExtractor()

# --- Pydantic Models ---
class URLRequest(BaseModel):
    url: str

class ClassificationResponse(BaseModel):
    url: str
    score: float
    risk_level: str
    explanation: str

# --- Response Logic ---
class ResponseGenerator:
    @staticmethod
    def get_risk_level(score: float) -> str:
        if score <= 1.0: return "SAFE"
        if score <= 3.0: return "SUSPICIOUS"
        return "PHISHING"

    @staticmethod
    def generate_explanation(features: Dict, score: float, risk_level: str) -> str:
        reasons = []
        if features.get('has_ip') == 1: reasons.append("uses a raw IP address instead of a domain name")
        if features.get('has_at_symbol') == 1: reasons.append("contains an '@' symbol")
        if features.get('num_hyphens', 0) >= 3: reasons.append("contains an unusually high number of hyphens")
        if features.get('domain_entropy', 0) > 3.5: reasons.append("has a highly random/complex domain name")
        if features.get('url_length', 0) > 80: reasons.append("is excessively long")
        
        if not reasons:
            return "The URL structure appears standard and matches legitimate website patterns." if risk_level == "SAFE" else "The URL exhibits minor anomalies but lacks definitive malicious traits."
        return f"This URL is classified as {risk_level.lower()} because it {', '.join(reasons)}."

response_gen = ResponseGenerator()

# --- API Endpoints ---
@app.post("/api/v1/check-url", response_model=ClassificationResponse)
async def check_url(request: URLRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not trained yet. Run training pipeline.")
    
    try:
        raw_features = extractor.extract_features(request.url)
        feature_vector = np.array([[raw_features.get(fname, 0) for fname in feature_names]])
        
        phishing_prob = model.predict_proba(feature_vector)[0][1] 
        score = round(phishing_prob * 5.0, 1) 
        risk_level = response_gen.get_risk_level(score)
        explanation = response_gen.generate_explanation(raw_features, score, risk_level)
        
        return ClassificationResponse(url=request.url, score=score, risk_level=risk_level, explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

# --- Serve React Frontend (Production) ---
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    # Serve static assets (JS/CSS)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Catch-all route to serve index.html for React Router (if used) or main app
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        # Prevent API routes from being caught here
        if full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("docs"):
            raise HTTPException(status_code=404)
            
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
