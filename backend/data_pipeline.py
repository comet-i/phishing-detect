# backend/data_pipeline.py
import os
import pandas as pd
import kaggle
from feature_extractor import FeatureExtractor

def ingest_and_preprocess_kaggle_dataset(dataset_slug: str = "siddharthkumarworks/phishing-website-dataset"):
    """
    Downloads dataset from Kaggle, preprocesses it, and saves it for training.
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
    """
    print(f"Downloading dataset: {dataset_slug}...")
    kaggle.api.dataset_download_files(dataset_slug, path='./data', unzip=True)
    
    # Assuming the downloaded file is named 'dataset.csv'
    df = pd.read_csv('./data/dataset.csv')
    
    # Basic cleaning
    df = df.dropna(subset=['URL', 'Result'])
    df['Result'] = df['Result'].apply(lambda x: 1 if x == 1 else 0) # Ensure binary 0/1
    
    # Extract features for the training set
    print("Extracting features for training data...")
    extractor = FeatureExtractor()
    X = df['URL'].apply(extractor.extract_features).apply(pd.Series)
    y = df['Result']
    
    # Save processed data
    X.to_csv('./data/X_train.csv', index=False)
    y.to_csv('./data/y_train.csv', index=False)
    print("Data ingestion and preprocessing complete.")

if __name__ == "__main__":
    os.makedirs('./data', exist_ok=True)
    ingest_and_preprocess_kaggle_dataset()
