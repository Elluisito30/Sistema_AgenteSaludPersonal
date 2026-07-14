"""
Dataset loader for UCI Obesity Dataset (id=544).

Fetches the raw dataset from UCI ML Repository via ucimlrepo.
Returns raw X (features) and y (target) as pandas DataFrames.
"""

import pandas as pd
from ucimlrepo import fetch_ucirepo

from config import UCI_DATASET_ID


def load_dataset():
    """
    Fetch UCI Obesity Dataset.

    Returns:
        tuple: (X_raw, y_raw) where both are pandas DataFrames.
               X_raw has 16 original columns, y_raw has 'NObeyesdad'.
    """
    obesity = fetch_ucirepo(id=UCI_DATASET_ID)
    X_raw = obesity.data.features
    y_raw = obesity.data.targets
    return X_raw, y_raw


def get_raw_feature_names():
    """Return list of original feature column names."""
    obesity = fetch_ucirepo(id=UCI_DATASET_ID)
    return list(obesity.data.features.columns)


def get_target_classes():
    """Return sorted list of unique target class labels."""
    obesity = fetch_ucirepo(id=UCI_DATASET_ID)
    y = obesity.data.targets.iloc[:, 0]
    return sorted(y.unique().tolist())


if __name__ == "__main__":
    X_raw, y_raw = load_dataset()
    print(f"Samples:  {len(X_raw)}")
    print(f"Features: {X_raw.shape[1]} raw columns")
    print(f"Classes:  {y_raw.iloc[:, 0].nunique()}")
    print(f"Targets:  {y_raw.iloc[:, 0].unique().tolist()}")
