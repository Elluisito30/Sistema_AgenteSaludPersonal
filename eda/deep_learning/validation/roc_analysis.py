"""
ROC curve analysis for multiclass classification.

Implements One-vs-Rest (OvR), Macro-average, and Micro-average ROC curves.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc


def compute_ovr_roc(y_true_onehot, y_pred_proba, class_names):
    """
    Compute One-vs-Rest ROC curves for each class.

    Args:
        y_true_onehot:  True labels as one-hot (np.ndarray, shape [n, n_classes]).
        y_pred_proba:   Predicted probabilities (np.ndarray, shape [n, n_classes]).
        class_names:    List of class name strings.
    """
    n_classes = len(class_names)
    results = {}

    for i in range(n_classes):
        fpr, tpr, _ = roc_curve(y_true_onehot[:, i], y_pred_proba[:, i])
        roc_auc = auc(fpr, tpr)
        results[class_names[i]] = {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "auc": round(float(roc_auc), 6),
        }
    return results


def compute_macro_roc(ovr_results, class_names):
    """Compute macro-average ROC curve."""
    all_fpr = np.unique(np.concatenate([np.array(ovr_results[c]["fpr"]) for c in class_names]))
    mean_tpr = np.zeros_like(all_fpr)

    for c in class_names:
        fpr = np.array(ovr_results[c]["fpr"])
        tpr = np.array(ovr_results[c]["tpr"])
        mean_tpr += np.interp(all_fpr, fpr, tpr)

    mean_tpr /= len(class_names)
    macro_auc = auc(all_fpr, mean_tpr)

    return {
        "fpr": all_fpr.tolist(),
        "tpr": mean_tpr.tolist(),
        "auc": round(float(macro_auc), 6),
    }


def compute_micro_roc(y_true_onehot, y_pred_proba):
    """Compute micro-average ROC curve."""
    y_true_flat = y_true_onehot.ravel()
    y_pred_flat = y_pred_proba.ravel()
    fpr, tpr, _ = roc_curve(y_true_flat, y_pred_flat)
    micro_auc = auc(fpr, tpr)

    return {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "auc": round(float(micro_auc), 6),
    }


def plot_roc_curves(ovr_results, macro_roc, micro_roc, class_names, output_path):
    """Plot all ROC curves on a single figure."""
    fig, ax = plt.subplots(figsize=(10, 8))

    colors = plt.cm.Set1(np.linspace(0, 1, len(class_names)))

    for i, cls in enumerate(class_names):
        fpr = ovr_results[cls]["fpr"]
        tpr = ovr_results[cls]["tpr"]
        auc_val = ovr_results[cls]["auc"]
        ax.plot(fpr, tpr, color=colors[i], lw=1.5,
                label=f"{cls} (AUC = {auc_val:.3f})")

    ax.plot(macro_roc["fpr"], macro_roc["tpr"], color="navy", lw=2.5, linestyle="--",
            label=f"Macro-avg (AUC = {macro_roc['auc']:.3f})")
    ax.plot(micro_roc["fpr"], micro_roc["tpr"], color="darkorange", lw=2.5, linestyle=":",
            label=f"Micro-avg (AUC = {micro_roc['auc']:.3f})")

    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5, label="Random")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("False Positive Rate", fontsize=12, fontweight="bold")
    ax.set_ylabel("True Positive Rate", fontsize=12, fontweight="bold")
    ax.set_title("Multiclass ROC Curves (One-vs-Rest)", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def run_roc_analysis(y_true, y_pred_proba, class_names, output_dir):
    """
    Full ROC analysis: OvR + Macro + Micro.

    Args:
        y_true:         True class indices (np.ndarray).
        y_pred_proba:   Predicted probabilities (np.ndarray, shape [n, n_classes]).
        class_names:    List of class name strings.
        output_dir:     Directory to save outputs.

    Returns:
        dict with ovr_results, macro_roc, micro_roc, path.
    """
    os.makedirs(output_dir, exist_ok=True)

    y_true_onehot = np.eye(len(class_names))[y_true]

    ovr_results = compute_ovr_roc(y_true_onehot, y_pred_proba, class_names)
    macro_roc = compute_macro_roc(ovr_results, class_names)
    micro_roc = compute_micro_roc(y_true_onehot, y_pred_proba)

    output_path = os.path.join(output_dir, "roc_curves.png")
    plot_roc_curves(ovr_results, macro_roc, micro_roc, class_names, output_path)

    return {
        "ovr": ovr_results,
        "macro": macro_roc,
        "micro": micro_roc,
        "path": output_path,
    }
