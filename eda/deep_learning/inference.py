"""
Inference module for the saved deep learning model.

Loads artifacts (model, scaler, label_encoder) and provides
prediction functions for new data.

Usage:
    from inference import load_artifacts, predict

    artifacts = load_artifacts("output/")
    result = predict(artifacts, features_dict)
"""

import os
import pickle
import numpy as np
import tensorflow as tf

from config import (
    FEATURE_COLUMNS, NUM_FEATURES,
    MODEL_FILENAME, SCALER_FILENAME, LABEL_ENCODER_FILENAME,
)


def load_artifacts(model_dir):
    """
    Load all saved artifacts from directory.

    Args:
        model_dir: Directory containing model .h5, scaler .pkl,
                   and label_encoder .pkl.

    Returns:
        dict: {
            'model': keras.Model,
            'scaler': StandardScaler,
            'label_encoder': LabelEncoder,
            'class_names': list[str],
        }
    """
    model_path = os.path.join(model_dir, MODEL_FILENAME)
    scaler_path = os.path.join(model_dir, SCALER_FILENAME)
    le_path = os.path.join(model_dir, LABEL_ENCODER_FILENAME)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler not found: {scaler_path}")
    if not os.path.exists(le_path):
        raise FileNotFoundError(f"Label encoder not found: {le_path}")

    model = tf.keras.models.load_model(model_path, compile=False)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    with open(le_path, "rb") as f:
        label_encoder = pickle.load(f)

    print(f"Artifacts loaded from: {model_dir}")
    print(f"  Model input shape:  {model.input_shape}")
    print(f"  Model output shape: {model.output_shape}")
    print(f"  Classes: {list(label_encoder.classes_)}")

    return {
        "model": model,
        "scaler": scaler,
        "label_encoder": label_encoder,
        "class_names": list(label_encoder.classes_),
    }


def _prepare_features_from_dict(features_dict):
    """
    Convert a feature dict to the expected 11-feature numpy array.

    Expected keys:
        Age, Gender, Height, Weight, SMOKE, FAF,
        BMI, family_history, FAVC, FCVC, CH2O

    Returns:
        np.ndarray of shape (1, 11).
    """
    row = []
    for col in FEATURE_COLUMNS:
        val = features_dict.get(col)
        if val is None:
            raise ValueError(f"Missing required feature: {col}")
        row.append(float(val))
    return np.array([row], dtype=np.float32)


def predict(artifacts, features_dict):
    """
    Predict obesity class for a single sample.

    Args:
        artifacts:     Dict from load_artifacts().
        features_dict: Dict with 11 feature key-value pairs.

    Returns:
        dict: {
            'predicted_class': str,
            'confidence': float,
            'probabilities': dict[class_name -> prob],
        }
    """
    model = artifacts["model"]
    scaler = artifacts["scaler"]
    le = artifacts["label_encoder"]

    X = _prepare_features_from_dict(features_dict)
    X_scaled = scaler.transform(X)

    proba = model.predict(X_scaled, verbose=0)[0]
    pred_idx = int(np.argmax(proba))
    pred_class = le.inverse_transform([pred_idx])[0]
    confidence = float(proba[pred_idx])

    proba_dict = {
        le.inverse_transform([i])[0]: float(proba[i])
        for i in range(len(proba))
    }

    return {
        "predicted_class": pred_class,
        "confidence": round(confidence, 6),
        "probabilities": proba_dict,
    }


def predict_batch(artifacts, features_list):
    """
    Predict for multiple samples.

    Args:
        artifacts:     Dict from load_artifacts().
        features_list: List of feature dicts.

    Returns:
        list[dict]: One prediction dict per sample.
    """
    return [predict(artifacts, f) for f in features_list]


if __name__ == "__main__":
    import sys

    model_dir = sys.argv[1] if len(sys.argv) > 1 else "output/"

    artifacts = load_artifacts(model_dir)

    sample = {
        "Age": 25, "Gender": 1, "Height": 1.75, "Weight": 80.0,
        "SMOKE": 0, "FAF": 1.0, "BMI": 26.12,
        "family_history": 1, "FAVC": 1, "FCVC": 3.0, "CH2O": 2.0,
    }

    result = predict(artifacts, sample)
    print(f"\nPrediction: {result['predicted_class']}")
    print(f"Confidence: {result['confidence']:.4f}")
    print("Probabilities:")
    for cls, prob in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
        print(f"  {cls}: {prob:.4f}")
