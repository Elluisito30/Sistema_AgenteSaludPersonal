"""
Model evaluation module.

Evaluates the best model on the held-out test set.
Produces metrics JSON (accuracy, balanced accuracy, F1, ROC-AUC,
confusion matrix, classification report).
"""

import os
import json
import numpy as np
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    precision_score, recall_score, roc_auc_score,
    confusion_matrix, classification_report,
)

from config import OUTPUT_DIR


def evaluate_model(model, X_test, y_test, class_names=None):
    """
    Evaluate a trained model on the test set.

    Args:
        model:     Trained keras.Model.
        X_test:    Scaled test features (np.ndarray).
        y_test:    True labels (np.ndarray).
        class_names: Optional list of class name strings.

    Returns:
        dict: Comprehensive metrics dictionary.
    """
    y_pred_proba = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)

    num_classes = len(class_names) if class_names else int(y_test.max()) + 1
    average_method = "macro" if num_classes > 2 else "binary"

    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average=average_method)
    precision = precision_score(y_test, y_pred, average=average_method)
    recall = recall_score(y_test, y_pred, average=average_method)

    try:
        roc_auc = roc_auc_score(
            y_test, y_pred_proba, multi_class="ovr", average=average_method
        )
    except ValueError:
        roc_auc = None

    cm = confusion_matrix(y_test, y_pred).tolist()
    report_str = classification_report(
        y_test, y_pred, target_names=class_names, digits=4
    )

    report_dict = classification_report(
        y_test, y_pred, target_names=class_names, output_dict=True, digits=4
    )

    metrics = {
        "accuracy": round(acc, 6),
        "balanced_accuracy": round(bal_acc, 6),
        "f1_macro": round(f1, 6),
        "precision_macro": round(precision, 6),
        "recall_macro": round(recall, 6),
        "roc_auc_ovr": round(roc_auc, 6) if roc_auc is not None else None,
        "confusion_matrix": cm,
        "classification_report": report_dict,
        "num_test_samples": int(len(y_test)),
        "num_classes": num_classes,
    }

    print("\n--- Test Set Evaluation ---")
    print(f"Accuracy:          {acc:.4f}")
    print(f"Balanced Accuracy: {bal_acc:.4f}")
    print(f"F1 Macro:          {f1:.4f}")
    print(f"Precision Macro:   {precision:.4f}")
    print(f"Recall Macro:      {recall:.4f}")
    if roc_auc is not None:
        print(f"ROC-AUC OvR:       {roc_auc:.4f}")
    print()
    print(report_str)

    return metrics


def save_metrics(metrics, output_dir=OUTPUT_DIR):
    """Save metrics dictionary to JSON."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "metrics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Metrics saved to {path}")
    return path
