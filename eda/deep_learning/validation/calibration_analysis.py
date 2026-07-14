"""
Calibration analysis.

Computes calibration curves (reliability diagrams) per class
and Brier Score.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve


def compute_brier_score(y_true, y_pred_proba, num_classes):
    """Compute macro-averaged Brier Score."""
    y_true_onehot = np.eye(num_classes)[y_true]
    brier_per_class = []
    for c in range(num_classes):
        brier = np.mean((y_pred_proba[:, c] - y_true_onehot[:, c]) ** 2)
        brier_per_class.append(round(float(brier), 6))
    macro_brier = round(float(np.mean(brier_per_class)), 6)
    return macro_brier, brier_per_class


def compute_calibration_curves(y_true, y_pred_proba, class_names):
    """Compute calibration curve data for each class."""
    n_classes = len(class_names)
    y_true_onehot = np.eye(n_classes)[y_true]
    results = {}

    for i, cls in enumerate(class_names):
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_true_onehot[:, i], y_pred_proba[:, i], n_bins=10, strategy="uniform"
        )
        results[cls] = {
            "fraction_of_positives": fraction_of_positives.tolist(),
            "mean_predicted_value": mean_predicted_value.tolist(),
        }
    return results


def plot_calibration_curves(calibration_data, class_names, output_path, brier_score):
    """Plot reliability diagrams per class."""
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.Set1(np.linspace(0, 1, len(class_names)))

    for i, cls in enumerate(class_names):
        fop = calibration_data[cls]["fraction_of_positives"]
        mpv = calibration_data[cls]["mean_predicted_value"]
        ax.plot(mpv, fop, "s-", color=colors[i], lw=1.5, markersize=5,
                label=f"{cls}")

    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5, label="Perfectly calibrated")
    ax.set_xlabel("Mean Predicted Probability", fontsize=12, fontweight="bold")
    ax.set_ylabel("Fraction of Positives", fontsize=12, fontweight="bold")
    ax.set_title(f"Calibration Curves (Brier Score = {brier_score:.4f})", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def run_calibration_analysis(y_true, y_pred_proba, class_names, output_dir):
    """
    Full calibration analysis.

    Returns:
        dict with brier_score, brier_per_class, calibration_data, path.
    """
    os.makedirs(output_dir, exist_ok=True)
    num_classes = len(class_names)

    brier_score, brier_per_class = compute_brier_score(y_true, y_pred_proba, num_classes)
    calibration_data = compute_calibration_curves(y_true, y_pred_proba, class_names)

    output_path = os.path.join(output_dir, "calibration_curve.png")
    plot_calibration_curves(calibration_data, class_names, output_path, brier_score)

    brier_per_class_dict = {class_names[i]: brier_per_class[i] for i in range(num_classes)}

    return {
        "brier_score": brier_score,
        "brier_per_class": brier_per_class_dict,
        "calibration_data": calibration_data,
        "path": output_path,
    }
