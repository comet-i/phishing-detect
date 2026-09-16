import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Use absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

def train_model():
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    x_path = os.path.join(DATA_DIR, 'X_train.csv')
    y_path = os.path.join(DATA_DIR, 'y_train.csv')
    
    if not os.path.exists(x_path) or not os.path.exists(y_path):
        raise FileNotFoundError(f"Training data not found at {DATA_DIR}. Run data_pipeline.py first.")
        
    print("Loading training data...")
    X = pd.read_csv(x_path)
    y = pd.read_csv(y_path)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest (max_depth=4)...")
    model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    
    print(f"Model Accuracy: {model.score(X_test, y_test):.4f}")
    
    # Save using absolute paths
    model_path = os.path.join(MODELS_DIR, 'phishing_rf_model.pkl')
    features_path = os.path.join(MODELS_DIR, 'feature_names.pkl')
    
    joblib.dump(model, model_path)
    joblib.dump(list(X.columns), features_path)
    print(f"Model saved to {MODELS_DIR}")

if __name__ == "__main__":
    train_model()
