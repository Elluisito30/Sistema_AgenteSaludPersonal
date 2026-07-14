"""
Confusion matrix analysis.

Computes normalized confusion matrix and generates a publication-quality plot.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix


def compute_confusion_matrix(y_true, y_pred, class_names):
    """Compute normalized (row-wise) confusion matrix."""
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
    cm_norm = np.nan_to_num(cm_norm)
    return cm, cm_norm


def plot_confusion_matrix(cm_norm, class_names, output_path, title="Normalized Confusion Matrix"):
    """Plot and save confusion matrix heatmap."""
    fig, ax = plt.subplots(figsize=(10, 8))

    sns.heatmap(
        cm_norm,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        linewidths=0.5,
        linecolor="gray",
        vmin=0,
        vmax=1,
        ax=ax,
    )

    ax.set_xlabel("Predicted Label", fontsize=12, fontweight="bold")
    ax.set_ylabel("True Label", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def run_confusion_analysis(y_true, y_pred, class_names, output_dir):
    """
    Full confusion analysis: compute + plot.

    Returns:
        dict with cm, cm_norm, per_class_recall, path.
    """
    os.makedirs(output_dir, exist_ok=True)
    cm, cm_norm = compute_confusion_matrix(y_true, y_pred, class_names)
    per_class_recall = {class_names[i]: round(float(cm_norm[i, i]), 4) for i in range(len(class_names))}

    output_path = os.path.join(output_dir, "confusion_matrix.png")
    plot_confusion_matrix(cm_norm, class_names, output_path)

    return {
        "cm": cm.tolist(),
        "cm_norm": np.round(cm_norm, 4).tolist(),
        "per_class_recall": per_class_recall,
        "path": output_path,
    }
