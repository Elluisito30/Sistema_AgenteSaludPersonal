"""
Training engine for Deep Learning experiments.

Trains all 24 MLP configurations via grid search.
Selects the best model based on validation accuracy.
Uses EarlyStopping, ReduceLROnPlateau, and ModelCheckpoint.
"""

import os
import time
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

from config import (
    RANDOM_SEED, MAX_EPOCHS, BATCH_SIZE, VERBOSE,
    EARLY_STOPPING_PATIENCE, EARLY_STOPPING_MIN_DELTA,
    REDUCE_LR_PATIENCE, REDUCE_LR_FACTOR, REDUCE_LR_MIN_LR,
    BEST_MODEL_METRIC, OUTPUT_DIR,
)
from build_models import build_model_from_config, generate_grid_configs


def _set_seeds():
    """Fix all random seeds for reproducibility."""
    np.random.seed(RANDOM_SEED)
    tf.random.set_seed(RANDOM_SEED)
    os.environ["PYTHONHASHSEED"] = str(RANDOM_SEED)


def train_single_model(config, num_features, num_classes, X_train, y_train, X_val, y_val):
    """
    Train one MLP configuration.

    Args:
        config:       Dict with architecture hyperparameters.
        num_features: Input dimension.
        num_classes:  Output classes.
        X_train, y_train: Training data.
        X_val, y_val:     Validation data.

    Returns:
        dict: {
            'config': config copy,
            'model': trained keras.Model,
            'history': keras.callbacks.History,
            'val_accuracy': best validation accuracy,
            'best_epoch': epoch with best val_accuracy,
            'train_time': seconds,
        }
    """
    _set_seeds()

    model = build_model_from_config(num_features, num_classes, config)

    checkpoint_path = os.path.join(OUTPUT_DIR, f"_temp_{config['name']}.keras")
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=EARLY_STOPPING_PATIENCE,
            min_delta=EARLY_STOPPING_MIN_DELTA,
            restore_best_weights=True,
            verbose=0,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=REDUCE_LR_FACTOR,
            patience=REDUCE_LR_PATIENCE,
            min_lr=REDUCE_LR_MIN_LR,
            verbose=0,
        ),
        keras.callbacks.ModelCheckpoint(
            checkpoint_path,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=0,
        ),
    ]

    start = time.time()
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=MAX_EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=VERBOSE,
    )
    elapsed = time.time() - start

    best_idx = int(np.argmax(history.history["val_accuracy"]))
    best_val_acc = float(history.history["val_accuracy"][best_idx])

    # Cleanup temp checkpoint
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    return {
        "config": config.copy(),
        "model": model,
        "history": history,
        "val_accuracy": best_val_acc,
        "best_epoch": best_idx + 1,
        "train_time": elapsed,
    }


def grid_search(num_features, num_classes, X_train, y_train, X_val, y_val):
    """
    Run full grid search over all configurations.

    Returns:
        tuple: (results: list[dict], best: dict)
               Results sorted by val_accuracy descending.
               Best is the top-performing configuration.
    """
    configs = generate_grid_configs()
    results = []

    print("=" * 80)
    print(f"GRID SEARCH: {len(configs)} configurations")
    print("=" * 80)

    for i, cfg in enumerate(configs, 1):
        print(f"\n[{i}/{len(configs)}] {cfg['name']}")
        print(f"  layers={cfg['hidden_units']} opt={cfg['optimizer']} "
              f"act={cfg['activation']} reg={cfg['regularization']}")

        result = train_single_model(
            cfg, num_features, num_classes,
            X_train, y_train, X_val, y_val,
        )

        print(f"  val_acc={result['val_accuracy']:.4f} "
              f"best_epoch={result['best_epoch']} "
              f"time={result['train_time']:.1f}s")

        results.append(result)

    results.sort(key=lambda r: r["val_accuracy"], reverse=True)

    best = results[0]
    print("\n" + "=" * 80)
    print(f"BEST MODEL: {best['config']['name']}")
    print(f"  val_accuracy = {best['val_accuracy']:.4f}")
    print(f"  best_epoch   = {best['best_epoch']}")
    print(f"  train_time   = {best['train_time']:.1f}s")
    print("=" * 80)

    return results, best


def save_grid_results(results, output_dir=OUTPUT_DIR):
    """Save grid search results to CSV."""
    os.makedirs(output_dir, exist_ok=True)
    rows = []
    for r in results:
        c = r["config"]
        rows.append({
            "name": c["name"],
            "hidden_units": str(c["hidden_units"]),
            "optimizer": c["optimizer"],
            "activation": c["activation"],
            "regularization": c["regularization"],
            "val_accuracy": r["val_accuracy"],
            "best_epoch": r["best_epoch"],
            "train_time_s": round(r["train_time"], 2),
        })
    df = pd.DataFrame(rows).sort_values("val_accuracy", ascending=False)
    path = os.path.join(output_dir, "grid_results.csv")
    df.to_csv(path, index=False)
    print(f"Grid results saved to {path}")
    return df


if __name__ == "__main__":
    print("This module is intended to be called from run_pipeline.py")
    print("Or import and call grid_search() directly.")
