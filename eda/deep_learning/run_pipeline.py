"""
Main pipeline orchestrator for Deep Learning experiments.

Executes the full pipeline:
    1. Load dataset
    2. Preprocess (features, scaling, splits)
    3. Grid search (24 MLP configurations)
    4. Evaluate best model on test set
    5. Save all artifacts

Usage:
    python run_pipeline.py              # full pipeline
    python run_pipeline.py --quick      # 3 configs only (debug)
"""

import os
import sys
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from config import OUTPUT_DIR
from dataset_loader import load_dataset
from preprocessing import prepare_full_pipeline
from train_models import grid_search, save_grid_results
from evaluate_models import evaluate_model
from save_best_model import save_all_artifacts


def run(quick=False):
    """
    Execute the full deep learning pipeline.

    Args:
        quick: If True, test only 3 configurations (for debugging).
    """
    start_total = time.time()

    print("=" * 80)
    print("DEEP LEARNING PIPELINE — Obesity Classification with MLPs")
    print("=" * 80)
    print(f"Output directory: {OUTPUT_DIR}\n")

    # 1. Load dataset
    print("[1/5] Loading dataset...")
    X_raw, y_raw = load_dataset()
    print(f"  Loaded {len(X_raw)} samples")

    # 2. Preprocess
    print("\n[2/5] Preprocessing...")
    data = prepare_full_pipeline(X_raw, y_raw)
    print(f"  Train: {data['X_train'].shape[0]} samples")
    print(f"  Val:   {data['X_val'].shape[0]} samples")
    print(f"  Test:  {data['X_test'].shape[0]} samples")
    print(f"  Features: {data['num_features']}")
    print(f"  Classes:  {data['num_classes']}")

    # 3. Grid search
    print("\n[3/5] Grid search...")
    if quick:
        from build_models import generate_grid_configs
        from train_models import train_single_model
        import numpy as np
        configs = generate_grid_configs()[:3]
        results = []
        for cfg in configs:
            print(f"\n  [quick] Training: {cfg['name']}")
            r = train_single_model(
                cfg, data["num_features"], data["num_classes"],
                data["X_train"], data["y_train"],
                data["X_val"], data["y_val"],
            )
            results.append(r)
        results.sort(key=lambda r: r["val_accuracy"], reverse=True)
        best = results[0]
    else:
        results, best = grid_search(
            data["num_features"], data["num_classes"],
            data["X_train"], data["y_train"],
            data["X_val"], data["y_val"],
        )

    # Save grid results
    save_grid_results(results)

    # 4. Evaluate best on test set
    print("\n[4/5] Evaluating best model on test set...")
    metrics = evaluate_model(
        best["model"], data["X_test"], data["y_test"],
        class_names=data["class_names"],
    )

    # 5. Save artifacts
    print("\n[5/5] Saving artifacts...")
    saved = save_all_artifacts(
        model=best["model"],
        history=best["history"],
        scaler=data["scaler"],
        label_encoder=data["label_encoder"],
        metrics=metrics,
        config=best["config"],
    )

    elapsed = time.time() - start_total
    print(f"\n{'=' * 80}")
    print(f"PIPELINE COMPLETE in {elapsed:.1f}s")
    print(f"{'=' * 80}")
    print(f"Best model: {best['config']['name']}")
    print(f"Test accuracy: {metrics['accuracy']:.4f}")
    print(f"Artifacts in:  {OUTPUT_DIR}")
    print(f"\nFiles:")
    for key, path in saved.items():
        print(f"  {key}: {path}")

    return best, metrics


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    run(quick=quick)
