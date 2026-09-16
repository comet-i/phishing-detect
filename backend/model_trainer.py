# backend/model_trainer.py
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def train_model():
    """Trains the Random Forest model with max_depth=4."""
    X = pd.read_csv('./data/X_train.csv')
    y = pd.read_csv('./data/y_train.csv')
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # "4 layers" interpreted as max_depth=4 for the decision trees
    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=4,       # Explicitly setting the 4 layers/depth
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    print(classification_report(y_test, preds))
    
    # Save model and feature names
    joblib.dump(model, './models/phishing_rf_model.pkl')
    joblib.dump(list(X.columns), './models/feature_names.pkl')
    print("Model trained and saved.")

if __name__ == "__main__":
    import os
    os.makedirs('./models', exist_ok=True)
    train_model()
