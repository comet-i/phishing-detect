# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import joblib
import numpy as np
from feature_extractor import FeatureExtractor
from typing import List, Dict

app = FastAPI(title="Phishing URL Classifier API", version="1.0.0")

# Load Model and Extractor at startup
model = joblib.load('./models/phishing_rf_model.pkl')
feature_names = joblib.load('./models/feature_names.pkl')
extractor = FeatureExtractor()

# --- Pydantic Models ---
class URLRequest(BaseModel):
    url: str

class ClassificationResponse(BaseModel):
    url: str
    score: float
    risk_level: str
    explanation: str

# --- Layer 4: Response Logic ---
class ResponseGenerator:
    @staticmethod
    def get_risk_level(score: float) -> str:
        if score <= 1.0: return "SAFE"
        if score <= 3.0: return "SUSPICIOUS"
        return "PHISHING"

    @staticmethod
    def generate_explanation(features: Dict, score: float, risk_level: str) -> str:
        """Generates a human-readable explanation based on feature thresholds."""
        reasons = []
        
        if features['has_ip'] == 1:
            reasons.append("uses a raw IP address instead of a domain name")
        if features['has_at_symbol'] == 1:
            reasons.append("contains an '@' symbol (often used to hide the true destination)")
        if features['num_hyphens'] >= 3:
            reasons.append("contains an unusually high number of hyphens")
        if features['domain_entropy'] > 3.5:
            reasons.append("has a highly random/complex domain name (possible DGA)")
        if features['url_length'] > 80:
            reasons.append("is excessively long")
            
        if not reasons:
            if risk_level == "SAFE":
                return "The URL structure appears standard and matches legitimate website patterns."
            return "The URL exhibits minor anomalies but lacks definitive malicious traits."

        return f"This URL is classified as {risk_level.lower()} because it {', '.join(reasons)}."

response_gen = ResponseGenerator()

# --- Layer 3 & 4: API Endpoints ---
@app.post("/api/v1/check-url", response_model=ClassificationResponse)
async def check_url(request: URLRequest):
    try:
        # 1. Feature Extraction (Layer 2)
        raw_features = extractor.extract_features(request.url)
        feature_vector = np.array([[raw_features[fname] for fname in feature_names]])
        
        # 2. Model Inference (Layer 3)
        # Get probability of being phishing (class 1)
        phishing_prob = model.predict_proba(feature_vector)[0][1] 
        
        # 3. Response Generation (Layer 4)
        # Map 0.0-1.0 probability to 0-5 score range
        score = round(phishing_prob * 5.0, 1) 
        risk_level = response_gen.get_risk_level(score)
        explanation = response_gen.generate_explanation(raw_features, score, risk_level)
        
        return ClassificationResponse(
            url=request.url,
            score=score,
            risk_level=risk_level,
            explanation=explanation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}
