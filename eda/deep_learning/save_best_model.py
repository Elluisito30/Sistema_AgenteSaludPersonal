"""
Artifact saver for the best model.

Saves:
    - best_model.h5       (Keras model weights + architecture)
    - history.pkl         (Training history object)
    - scaler.pkl          (Fitted StandardScaler)
    - label_encoder.pkl   (Fitted LabelEncoder)
    - metrics.json        (Test set evaluation metrics)
    - grid_results.csv    (All configurations ranked by val_accuracy)
"""

import os
import pickle
import json

from config import (
    OUTPUT_DIR,
    MODEL_FILENAME, HISTORY_FILENAME,
    SCALER_FILENAME, LABEL_ENCODER_FILENAME,
    METRICS_FILENAME, GRID_RESULTS_FILENAME,
)


def save_model(model, output_dir=OUTPUT_DIR):
    """Save Keras model to .h5 file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, MODEL_FILENAME)
    model.save(path)
    print(f"Model saved to {path}")
    return path


def save_history(history, output_dir=OUTPUT_DIR):
    """Save training history to .pkl file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, HISTORY_FILENAME)
    with open(path, "wb") as f:
        pickle.dump(history.history, f)
    print(f"History saved to {path}")
    return path


def save_scaler(scaler, output_dir=OUTPUT_DIR):
    """Save fitted StandardScaler to .pkl file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, SCALER_FILENAME)
    with open(path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"Scaler saved to {path}")
    return path


def save_label_encoder(label_encoder, output_dir=OUTPUT_DIR):
    """Save fitted LabelEncoder to .pkl file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, LABEL_ENCODER_FILENAME)
    with open(path, "wb") as f:
        pickle.dump(label_encoder, f)
    print(f"Label encoder saved to {path}")
    return path


def save_all_artifacts(model, history, scaler, label_encoder, metrics, config,
                       output_dir=OUTPUT_DIR):
    """
    Save all artifacts in one call.

    Args:
        model:          Trained keras.Model.
        history:        keras.callbacks.History.
        scaler:         Fitted StandardScaler.
        label_encoder:  Fitted LabelEncoder.
        metrics:        Dict from evaluate_models.evaluate_model().
        config:         Best model config dict.
        output_dir:     Output directory.

    Returns:
        dict: Paths of all saved files.
    """
    os.makedirs(output_dir, exist_ok=True)

    saved = {}
    saved["model"] = save_model(model, output_dir)
    saved["history"] = save_history(history, output_dir)
    saved["scaler"] = save_scaler(scaler, output_dir)
    saved["label_encoder"] = save_label_encoder(label_encoder, output_dir)
    saved["metrics"] = save_metrics(metrics, output_dir)

    # Save best config alongside metrics
    config_path = os.path.join(output_dir, "best_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    saved["config"] = config_path
    print(f"Best config saved to {config_path}")

    print(f"\nAll artifacts saved to: {output_dir}")
    return saved


def save_metrics(metrics, output_dir=OUTPUT_DIR):
    """Save metrics dictionary to JSON."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, METRICS_FILENAME)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Metrics saved to {path}")
    return path
