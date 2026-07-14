"""
Precision-Recall analysis per class.

Computes and plots Precision-Recall curves for each class.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, average_precision_score


def compute_precision_recall_curves(y_true, y_pred_proba, class_names):
    """Compute per-class Precision-Recall curves."""
    n_classes = len(class_names)
    y_true_onehot = np.eye(n_classes)[y_true]
    results = {}

    for i, cls in enumerate(class_names):
        precision, recall, thresholds = precision_recall_curve(
            y_true_onehot[:, i], y_pred_proba[:, i]
        )
        avg_precision = average_precision_score(y_true_onehot[:, i], y_pred_proba[:, i])
        results[cls] = {
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "avg_precision": round(float(avg_precision), 6),
        }
    return results


def plot_precision_recall_curves(pr_data, class_names, output_path):
    """Plot Precision-Recall curves per class."""
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.Set1(np.linspace(0, 1, len(class_names)))

    for i, cls in enumerate(class_names):
        precision = pr_data[cls]["precision"]
        recall = pr_data[cls]["recall"]
        ap = pr_data[cls]["avg_precision"]
        ax.plot(recall, precision, color=colors[i], lw=1.5,
                label=f"{cls} (AP = {ap:.3f})")

    ax.set_xlabel("Recall", fontsize=12, fontweight="bold")
    ax.set_ylabel("Precision", fontsize=12, fontweight="bold")
    ax.set_title("Precision-Recall Curves (One-vs-Rest)", fontsize=14, fontweight="bold")
    ax.legend(loc="lower left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def run_precision_recall_analysis(y_true, y_pred_proba, class_names, output_dir):
    """
    Full Precision-Recall analysis.

    Returns:
        dict with per_class results and path.
    """
    os.makedirs(output_dir, exist_ok=True)
    pr_data = compute_precision_recall_curves(y_true, y_pred_proba, class_names)

    output_path = os.path.join(output_dir, "precision_recall.png")
    plot_precision_recall_curves(pr_data, class_names, output_path)

    return {
        "per_class": pr_data,
        "macro_avg_precision": round(float(np.mean([pr_data[c]["avg_precision"] for c in class_names])), 6),
        "path": output_path,
    }
