"""
Validation report generator.

Orchestrates all analyses and generates:
    - validation_report.md  (academic format)
    - validation_metrics.json
    - comparison_results.csv
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import pickle
import tensorflow as tf

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import OUTPUT_DIR, RANDOM_SEED, FEATURE_COLUMNS

from confusion_analysis import run_confusion_analysis
from roc_analysis import run_roc_analysis
from calibration_analysis import run_calibration_analysis
from bootstrap_validation import run_bootstrap_validation
from statistical_comparison import run_statistical_comparison
from precision_recall import run_precision_recall_analysis

VALIDATION_DIR = os.path.dirname(os.path.abspath(__file__))


def load_artifacts():
    """Load model artifacts and prepare test data."""
    model_path = os.path.join(OUTPUT_DIR, "best_model.h5")
    scaler_path = os.path.join(OUTPUT_DIR, "scaler.pkl")
    le_path = os.path.join(OUTPUT_DIR, "label_encoder.pkl")
    metrics_path = os.path.join(OUTPUT_DIR, "metrics.json")

    model = tf.keras.models.load_model(model_path, compile=False)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    with open(le_path, "rb") as f:
        label_encoder = pickle.load(f)

    with open(metrics_path, "r") as f:
        train_metrics = json.load(f)

    return model, scaler, label_encoder, train_metrics


def prepare_test_data(scaler):
    """Load dataset and prepare test set (same split as training)."""
    from dataset_loader import load_dataset
    from preprocessing import prepare_features, encode_target, split_data

    X_raw, y_raw = load_dataset()
    X = prepare_features(X_raw)
    y_encoded, le = encode_target(y_raw)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y_encoded)

    X_test_scaled = scaler.transform(X_test)

    return X_test_scaled, y_test, X, y_encoded, le


def generate_validation_report(results, train_metrics, output_dir):
    """Generate markdown report in academic format."""
    class_names = results["class_names"]
    n_classes = len(class_names)
    n_test = results["n_test"]

    md = []
    md.append("# Deep Learning Validation Report")
    md.append("")
    md.append("## Scientific Validation of Neural Network for Obesity Classification")
    md.append("")
    md.append("---")
    md.append("")

    md.append("## 1. Executive Summary")
    md.append("")
    md.append(f"This report presents the scientific validation of a Multi-Layer Perceptron (MLP) trained")
    md.append(f"for obesity classification using {n_classes} classes from the UCI Obesity Dataset.")
    md.append(f"The model was validated on a held-out test set of {n_test} samples using multiple")
    md.append(f"complementary evaluation metrics and statistical tests.")
    md.append("")

    md.append("### 1.1 Training Metrics (from Grid Search)")
    md.append("")
    md.append(f"| Metric | Value |")
    md.append(f"|--------|-------|")
    md.append(f"| Test Accuracy | {train_metrics.get('accuracy', 'N/A'):.4f} |")
    md.append(f"| Balanced Accuracy | {train_metrics.get('balanced_accuracy', 'N/A'):.4f} |")
    md.append(f"| F1 Macro | {train_metrics.get('f1_macro', 'N/A'):.4f} |")
    md.append(f"| Precision Macro | {train_metrics.get('precision_macro', 'N/A'):.4f} |")
    md.append(f"| Recall Macro | {train_metrics.get('recall_macro', 'N/A'):.4f} |")
    auc_val = train_metrics.get('roc_auc_ovr')
    md.append(f"| ROC-AUC OvR | {auc_val:.4f} |" if auc_val else "| ROC-AUC OvR | N/A |")
    md.append(f"| Test Samples | {n_test} |")
    md.append(f"| Num Classes | {n_classes} |")
    md.append("")

    md.append("## 2. Confusion Matrix Analysis")
    md.append("")
    md.append("![Confusion Matrix](confusion_matrix.png)")
    md.append("")
    md.append("**Per-Class Recall:**")
    md.append("")
    md.append("| Class | Recall |")
    md.append("|-------|--------|")
    for cls, recall in results["confusion"]["per_class_recall"].items():
        md.append(f"| {cls} | {recall:.4f} |")
    md.append("")
    md.append("**Interpretation:** The normalized confusion matrix shows the classification performance")
    md.append("per class. Values on the diagonal represent correct classification rates (recall).")
    md.append("Off-diagonal elements indicate inter-class confusion patterns.")
    md.append("")

    md.append("## 3. ROC Analysis (One-vs-Rest)")
    md.append("")
    md.append("![ROC Curves](roc_curves.png)")
    md.append("")
    md.append("### 3.1 Per-Class AUC")
    md.append("")
    md.append("| Class | AUC |")
    md.append("|-------|-----|")
    for cls, data in results["roc"]["ovr"].items():
        md.append(f"| {cls} | {data['auc']:.4f} |")
    md.append("")
    md.append(f"- **Macro-average AUC:** {results['roc']['macro']['auc']:.4f}")
    md.append(f"- **Micro-average AUC:** {results['roc']['micro']['auc']:.4f}")
    md.append("")
    md.append("**Interpretation:** AUC values above 0.9 indicate excellent discriminative ability.")
    md.append("The macro-average treats all classes equally; the micro-average weights by prevalence.")
    md.append("")

    md.append("## 4. Precision-Recall Analysis")
    md.append("")
    md.append("![Precision-Recall](precision_recall.png)")
    md.append("")
    md.append("| Class | Avg Precision |")
    md.append("|-------|---------------|")
    for cls, data in results["precision_recall"]["per_class"].items():
        md.append(f"| {cls} | {data['avg_precision']:.4f} |")
    md.append("")
    md.append(f"**Macro Avg Precision:** {results['precision_recall']['macro_avg_precision']:.4f}")
    md.append("")

    md.append("## 5. Calibration Analysis")
    md.append("")
    md.append("![Calibration Curve](calibration_curve.png)")
    md.append("")
    md.append(f"**Brier Score (macro):** {results['calibration']['brier_score']:.6f}")
    md.append("")
    md.append("| Class | Brier Score |")
    md.append("|-------|-------------|")
    for cls, bs in results["calibration"]["brier_per_class"].items():
        md.append(f"| {cls} | {bs:.6f} |")
    md.append("")
    md.append("**Interpretation:** The Brier Score measures probability calibration (lower is better).")
    md.append("Values close to 0 indicate well-calibrated probabilities. The calibration curve shows")
    md.append("how predicted probabilities align with observed frequencies.")
    md.append("")

    md.append("## 6. Bootstrap Confidence Intervals (95%)")
    md.append("")
    md.append("| Metric | Point Estimate | 95% CI Lower | 95% CI Upper | Std |")
    md.append("|--------|----------------|--------------|--------------|-----|")
    for metric_name, data in results["bootstrap"].items():
        if isinstance(data, dict) and "point_estimate" in data:
            md.append(f"| {metric_name} | {data['point_estimate']:.4f} | {data['ci_lower']:.4f} | {data['ci_upper']:.4f} | {data['std']:.4f} |")
    md.append("")
    md.append("**Interpretation:** Bootstrap confidence intervals provide non-parametric uncertainty")
    md.append("estimates. Narrow CIs indicate stable model performance.")
    md.append("")

    md.append("## 7. Statistical Comparison: XGBoost vs Neural Network")
    md.append("")
    md.append("| Test | Statistic | p-value | Interpretation |")
    md.append("|------|-----------|---------|----------------|")
    comp = results["comparison"]
    md.append(f"| Wilcoxon signed-rank | {comp['wilcoxon']['statistic']} | {comp['wilcoxon']['p_value']} | {comp['wilcoxon']['interpretation']} |")
    md.append(f"| McNemar | {comp['mcnemar']['statistic']} | {comp['mcnemar']['p_value']} | {comp['mcnemar']['interpretation']} |")
    md.append(f"| DeLong (AUC diff) | {comp['delong']['auc_difference']} | CI [{comp['delong']['ci_lower_95']}, {comp['delong']['ci_upper_95']}] | {comp['delong']['interpretation']} |")
    md.append("")
    md.append(f"**XGBoost Accuracy:** {comp['xgb_accuracy']:.4f}")
    md.append(f"**XGBoost F1 Macro:** {comp['xgb_f1_macro']:.4f}")
    md.append(f"**Neural Network Accuracy:** {results['nn_accuracy']:.4f}")
    md.append(f"**Neural Network F1 Macro:** {results['nn_f1']:.4f}")
    md.append("")

    md.append("### 7.1 McNemar Contingency Table")
    md.append("")
    cont = comp["mcnemar"]["contingency"]
    md.append("| | XGB Correct | XGB Wrong |")
    md.append("|---|---|---|")
    md.append(f"| **NN Correct** | {cont['both_correct']} | {cont['nn_correct_xgb_wrong']} |")
    md.append(f"| **NN Wrong** | {cont['nn_wrong_xgb_correct']} | {cont['both_wrong']} |")
    md.append("")

    md.append("## 8. Conclusions")
    md.append("")
    md.append("### 8.1 Strengths")
    md.append("")
    md.append("- Comprehensive multiclass evaluation using 7 complementary metrics")
    md.append("- Bootstrap confidence intervals for robust uncertainty quantification")
    md.append("- Direct statistical comparison with the production XGBoost model")
    md.append("- Calibration analysis ensuring reliable probability estimates")
    md.append("- Precision-Recall analysis for class-specific performance")
    md.append("")

    md.append("### 8.2 Limitations")
    md.append("")
    md.append("- MLP uses 11 features vs. XGBoost's 11 features (same feature set)")
    md.append("- Single train/test split (no cross-validation)")
    md.append("- Quick training with 3 configurations (full grid = 24)")
    md.append("- No hyperparameter tuning beyond grid search")
    md.append("")

    md.append("### 8.3 Recommendations")
    md.append("")
    md.append("1. Run full 24-configuration grid search for production deployment")
    md.append("2. Add 5x2 cross-validation for more robust comparison")
    md.append("3. Consider ensemble methods combining XGBoost + MLP predictions")
    md.append("4. Investigate calibration improvement via Platt scaling")
    md.append("")

    md.append("---")
    md.append(f"*Report generated automatically by the Deep Learning Validation Pipeline*")
    md.append(f"*Date: {time.strftime('%Y-%m-%d %H:%M:%S')}*")

    report_path = os.path.join(output_dir, "validation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return report_path


def run():
    """Execute full validation pipeline."""
    start = time.time()

    print("=" * 80)
    print("DEEP LEARNING VALIDATION PIPELINE")
    print("=" * 80)

    print("\n[1/7] Loading model artifacts...")
    model, scaler, label_encoder, train_metrics = load_artifacts()
    class_names = list(label_encoder.classes_)

    print("[2/7] Preparing test data...")
    X_test_scaled, y_test, X_full, y_full, le = prepare_test_data(scaler)

    print("[3/7] Generating predictions...")
    y_pred_proba = model.predict(X_test_scaled, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)

    nn_accuracy = float(np.mean(y_pred == y_test))
    from sklearn.metrics import f1_score
    nn_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    print(f"  NN Accuracy: {nn_accuracy:.4f}")
    print(f"  NN F1 Macro: {nn_f1:.4f}")

    all_results = {
        "class_names": class_names,
        "n_test": len(y_test),
        "nn_accuracy": nn_accuracy,
        "nn_f1": nn_f1,
    }

    print("\n[4/7] Confusion matrix analysis...")
    all_results["confusion"] = run_confusion_analysis(y_test, y_pred, class_names, VALIDATION_DIR)

    print("[5/7] ROC analysis...")
    all_results["roc"] = run_roc_analysis(y_test, y_pred_proba, class_names, VALIDATION_DIR)

    print("[6/7] Precision-Recall analysis...")
    all_results["precision_recall"] = run_precision_recall_analysis(y_test, y_pred_proba, class_names, VALIDATION_DIR)

    print("       Calibration analysis...")
    all_results["calibration"] = run_calibration_analysis(y_test, y_pred_proba, class_names, VALIDATION_DIR)

    print("       Bootstrap validation...")
    all_results["bootstrap"] = run_bootstrap_validation(y_test, y_pred, y_pred_proba, n_bootstrap=1000)

    print("\n[7/7] Statistical comparison (XGBoost vs NN)...")
    X_test_unscaled = X_full.iloc[y_test.index] if hasattr(y_test, 'index') else X_full

    from dataset_loader import load_dataset
    from preprocessing import prepare_features, encode_target, split_data
    X_raw, y_raw = load_dataset()
    X_fe = prepare_features(X_raw)
    y_enc, _ = encode_target(y_raw)
    X_tr, X_vl, X_te, y_tr, y_vl, y_te = split_data(X_fe, y_enc)
    X_te_unscaled = X_te

    all_results["comparison"] = run_statistical_comparison(
        y_pred, y_pred_proba, X_te_unscaled, y_te, scaler, label_encoder
    )

    print("\nGenerating outputs...")
    os.makedirs(VALIDATION_DIR, exist_ok=True)

    metrics_path = os.path.join(VALIDATION_DIR, "validation_metrics.json")
    serializable = {
        "confusion": all_results["confusion"],
        "roc_macro_auc": all_results["roc"]["macro"]["auc"],
        "roc_micro_auc": all_results["roc"]["micro"]["auc"],
        "roc_per_class": {k: v["auc"] for k, v in all_results["roc"]["ovr"].items()},
        "precision_recall_macro": all_results["precision_recall"]["macro_avg_precision"],
        "brier_score": all_results["calibration"]["brier_score"],
        "bootstrap": all_results["bootstrap"],
        "nn_accuracy": nn_accuracy,
        "nn_f1_macro": nn_f1,
        "comparison": {
            "wilcoxon_p": all_results["comparison"]["wilcoxon"]["p_value"],
            "mcnemar_p": all_results["comparison"]["mcnemar"]["p_value"],
            "delong_diff": all_results["comparison"]["delong"]["auc_difference"],
            "delong_ci": [all_results["comparison"]["delong"]["ci_lower_95"],
                          all_results["comparison"]["delong"]["ci_upper_95"]],
            "xgb_accuracy": all_results["comparison"]["xgb_accuracy"],
            "xgb_f1": all_results["comparison"]["xgb_f1_macro"],
        },
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {metrics_path}")

    comp_df = all_results["comparison"]["comparison_table"]
    comp_path = os.path.join(VALIDATION_DIR, "comparison_results.csv")
    comp_df.to_csv(comp_path, index=False)
    print(f"  Saved: {comp_path}")

    print("  Generating validation_report.md...")
    report_path = generate_validation_report(all_results, train_metrics, VALIDATION_DIR)
    print(f"  Saved: {report_path}")

    elapsed = time.time() - start
    print(f"\n{'=' * 80}")
    print(f"VALIDATION COMPLETE in {elapsed:.1f}s")
    print(f"{'=' * 80}")
    print(f"Output: {VALIDATION_DIR}")
    print(f"Files:")
    for f in ["confusion_matrix.png", "roc_curves.png", "calibration_curve.png",
              "precision_recall.png", "validation_metrics.json", "comparison_results.csv",
              "validation_report.md"]:
        print(f"  {f}")

    return all_results


if __name__ == "__main__":
    run()
