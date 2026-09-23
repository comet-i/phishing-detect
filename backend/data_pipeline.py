import glob
import os

import pandas as pd
from .feature_extractor import FeatureExtractor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def ingest_and_preprocess_kaggle_dataset(dataset_slug: str = "shashwatwork/phishing-website-dataset"):
    # Kaggle is intentionally imported only when this offline training command runs.
    # Render production builds use the committed model and do not need Kaggle credentials.
    try:
        import kaggle
    except ImportError as exc:
        raise RuntimeError("Install kaggle locally to run the training pipeline.") from exc

    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Downloading dataset: {dataset_slug}...")
    try:
        kaggle.api.dataset_download_files(dataset_slug, path=DATA_DIR, unzip=True)
    except Exception as exc:
        raise RuntimeError(
            "Kaggle download failed. Configure Kaggle credentials before running this command."
        ) from exc

    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}.")

    df = pd.read_csv(csv_files[0])
    url_col = next((col for col in df.columns if "url" in col.lower()), df.columns[0])
    label_col = next(
        (col for col in df.columns if any(token in col.lower() for token in ("label", "result", "class"))),
        df.columns[1],
    )
    df = df.dropna(subset=[url_col, label_col])
    labels = {"1", "phishing", "bad", "true"}
    df[label_col] = df[label_col].apply(lambda value: int(str(value).strip().lower() in labels))

    extractor = FeatureExtractor()
    X = pd.DataFrame([extractor.extract_features(url) for url in df[url_col]])
    X.to_csv(os.path.join(DATA_DIR, "X_train.csv"), index=False)
    df[label_col].to_csv(os.path.join(DATA_DIR, "y_train.csv"), index=False)
    print(f"Data successfully saved to {DATA_DIR}")


if __name__ == "__main__":
    ingest_and_preprocess_kaggle_dataset()
