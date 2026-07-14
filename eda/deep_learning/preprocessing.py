"""
Preprocessing pipeline for Deep Learning experiments.

Handles feature engineering (11 features), target encoding,
StandardScaler fitting, and train/val/test splitting.

IMPORTANT: Scaler is fit ONLY on training data to prevent leakage.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from config import (
    FEATURE_COLUMNS, TARGET_COLUMN, RANDOM_SEED,
    TEST_SIZE, VAL_SIZE,
)


def prepare_features(X_raw):
    """
    Engineer the 11 features from the raw UCI dataset.

    Args:
        X_raw: Raw DataFrame with original 16 columns.

    Returns:
        pd.DataFrame with exactly FEATURE_COLUMNS.
    """
    X = pd.DataFrame()
    X["Age"] = X_raw["Age"]
    X["Gender"] = X_raw["Gender"].map({"male": 1, "female": 0, "Male": 1, "Female": 0})
    X["Height"] = X_raw["Height"]
    X["Weight"] = X_raw["Weight"]
    X["SMOKE"] = X_raw["SMOKE"].map({"yes": 1, "no": 0})
    X["FAF"] = X_raw["FAF"]
    X["BMI"] = X_raw["Weight"] / (X_raw["Height"] ** 2)
    X["family_history"] = X_raw["family_history_with_overweight"].map({"yes": 1, "no": 0})
    X["FAVC"] = X_raw["FAVC"].map({"yes": 1, "no": 0})
    X["FCVC"] = X_raw["FCVC"]
    X["CH2O"] = X_raw["CH2O"]
    return X[FEATURE_COLUMNS]


def encode_target(y_raw):
    """
    Fit LabelEncoder on target and return encoded labels + encoder.

    Args:
        y_raw: Series or DataFrame with target column.

    Returns:
        tuple: (y_encoded: np.ndarray, label_encoder: LabelEncoder)
    """
    y = y_raw.iloc[:, 0] if hasattr(y_raw, "iloc") else y_raw
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    return y_encoded, le


def split_data(X, y):
    """
    Split into train / val / test sets (stratified).

    Split ratios:
        15% test  ->  held out permanently
        15% val   ->  from remaining 85%
        ~72% train ->  remaining

    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    X_rest, X_test, y_rest, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_SEED
    )
    relative_val = VAL_SIZE / (1 - TEST_SIZE)
    X_train, X_val, y_train, y_val = train_test_split(
        X_rest, y_rest, test_size=relative_val, stratify=y_rest, random_state=RANDOM_SEED
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def fit_scaler(X_train):
    """
    Fit StandardScaler on training data only.

    Returns:
        tuple: (scaler: StandardScaler, X_train_scaled: np.ndarray)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    return scaler, X_train_scaled


def transform_with_scaler(scaler, X):
    """Transform data using a pre-fitted scaler."""
    return scaler.transform(X)


def prepare_full_pipeline(X_raw, y_raw):
    """
    Complete preprocessing pipeline.

    Returns:
        dict with all artifacts needed for training and inference.
    """
    X = prepare_features(X_raw)
    y_encoded, le = encode_target(y_raw)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y_encoded)
    scaler, X_train_scaled = fit_scaler(X_train)
    X_val_scaled = transform_with_scaler(scaler, X_val)
    X_test_scaled = transform_with_scaler(scaler, X_test)

    return {
        "X_train": X_train_scaled,
        "X_val": X_val_scaled,
        "X_test": X_test_scaled,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
        "scaler": scaler,
        "label_encoder": le,
        "feature_names": FEATURE_COLUMNS,
        "class_names": list(le.classes_),
        "num_features": X_train_scaled.shape[1],
        "num_classes": len(le.classes_),
    }


if __name__ == "__main__":
    from dataset_loader import load_dataset

    X_raw, y_raw = load_dataset()
    data = prepare_full_pipeline(X_raw, y_raw)
    print(f"Train: {data['X_train'].shape}")
    print(f"Val:   {data['X_val'].shape}")
    print(f"Test:  {data['X_test'].shape}")
    print(f"Classes ({data['num_classes']}): {data['class_names']}")
