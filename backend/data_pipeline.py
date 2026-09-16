import os
import pandas as pd
import kaggle
import glob
from feature_extractor import FeatureExtractor

# Use absolute paths based on this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def ingest_and_preprocess_kaggle_dataset(dataset_slug: str = "shashwatwork/phishing-website-dataset"):
    # 1. Ensure directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print(f"Downloading dataset: {dataset_slug}...")
    try:
        kaggle.api.dataset_download_files(dataset_slug, path=DATA_DIR, unzip=True)
    except Exception as e:
        raise RuntimeError(f"Kaggle download failed. Check credentials and dataset slug. Error: {e}")
    
    # 2. Find the downloaded CSV dynamically
    csv_files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}. Check Kaggle dataset slug.")
    
    csv_path = csv_files[0]
    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # 3. Dynamically find URL and Label columns (handles different dataset formats)
    url_col = next((col for col in df.columns if 'url' in col.lower()), df.columns[0])
    label_col = next((col for col in df.columns if 'label' in col.lower() or 'result' in col.lower() or 'class' in col.lower()), df.columns[1])
    
    df = df.dropna(subset=[url_col, label_col])
    # Normalize labels to 0 (safe) and 1 (phishing)
    df[label_col] = df[label_col].apply(lambda x: 1 if str(x).strip().lower() in ['1', 'phishing', 'bad', 'true'] else 0)
    
    print("Extracting features...")
    extractor = FeatureExtractor()
    features_list = [extractor.extract_features(url) for url in df[url_col]]
    
    X = pd.DataFrame(features_list)
    y = df[label_col]
    
    # 4. Save using absolute paths
    x_path = os.path.join(DATA_DIR, 'X_train.csv')
    y_path = os.path.join(DATA_DIR, 'y_train.csv')
    
    X.to_csv(x_path, index=False)
    y.to_csv(y_path, index=False)
    print(f"Data successfully saved to {DATA_DIR}")

if __name__ == "__main__":
    ingest_and_preprocess_kaggle_dataset()
