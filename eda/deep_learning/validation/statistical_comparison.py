"""
Statistical comparison between XGBoost and Neural Network.

Tests:
    - Wilcoxon signed-rank test (per-sample probability comparison)
    - McNemar test (binary disagreement comparison)
    - DeLong test (ROC-AUC difference)
"""

import os
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from scipy import stats
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import (
    MODELS_DIR, RANDOM_SEED, TEST_SIZE, VAL_SIZE,
    FEATURE_COLUMNS, RANDOM_SEED,
)


def load_xgboost_artifacts():
    """Load XGBoost model and label encoder."""
    model_path = os.path.join(MODELS_DIR, "xgb_11f.bin")
    le_path = os.path.join(MODELS_DIR, "le_target_11f.pkl")

    model = xgb.XGBClassifier()
    model.load_model(model_path)

    with open(le_path, "rb") as f:
        le = joblib.load(f)

    return model, le


def get_xgboost_predictions(xgb_model, X_test):
    """Get XGBoost predictions and probabilities."""
    y_pred = xgb_model.predict(X_test)
    y_proba = xgb_model.predict_proba(X_test)
    return y_pred, y_proba


def wilcoxon_test(y_pred_proba_nn, y_pred_proba_xgb, y_true):
    """
    Wilcoxon signed-rank test on per-sample max probability.

    Tests whether the two models produce significantly different
    prediction confidence distributions.
    """
    max_conf_nn = np.max(y_pred_proba_nn, axis=1)
    max_conf_xgb = np.max(y_pred_proba_xgb, axis=1)

    diff = max_conf_nn - max_conf_xgb
    diff = diff[diff != 0]

    if len(diff) < 10:
        return {"statistic": None, "p_value": None, "interpretation": "Insufficient non-zero differences"}

    stat, p_value = stats.wilcoxon(diff, alternative="two-sided")

    return {
        "statistic": round(float(stat), 6),
        "p_value": round(float(p_value), 8),
        "interpretation": (
            "Significant difference (p < 0.05)" if p_value < 0.05
            else "No significant difference (p >= 0.05)"
        ),
        "n_samples": len(diff),
        "mean_diff": round(float(np.mean(diff)), 6),
    }


def mcnemar_test(y_pred_nn, y_pred_xgb, y_true):
    """
    McNemar's test for comparing two classifiers.

    Contingency table:
        b00: both correct
        b01: NN wrong, XGB correct
        b10: NN correct, XGB wrong
        b11: both wrong
    """
    nn_correct = (y_pred_nn == y_true)
    xgb_correct = (y_pred_xgb == y_true)

    b01 = int(np.sum(~nn_correct & xgb_correct))
    b10 = int(np.sum(nn_correct & ~xgb_correct))
    b00 = int(np.sum(nn_correct & xgb_correct))
    b11 = int(np.sum(~nn_correct & ~xgb_correct))

    n_discordant = b01 + b10

    if n_discordant == 0:
        return {
            "statistic": 0, "p_value": 1.0,
            "interpretation": "No discordant pairs",
            "contingency": {"both_correct": b00, "nn_wrong_xgb_correct": b01,
                            "nn_correct_xgb_wrong": b10, "both_wrong": b11},
        }

    if n_discordant < 25:
        stat = (abs(b01 - b10) - 1) ** 2 / (b01 + b10)
    else:
        stat = (b01 - b10) ** 2 / (b01 + b10)

    p_value = 1 - stats.chi2.cdf(stat, df=1)

    return {
        "statistic": round(float(stat), 6),
        "p_value": round(float(p_value), 8),
        "interpretation": (
            "Significant difference (p < 0.05)" if p_value < 0.05
            else "No significant difference (p >= 0.05)"
        ),
        "contingency": {
            "both_correct": b00,
            "nn_wrong_xgb_correct": b01,
            "nn_correct_xgb_wrong": b10,
            "both_wrong": b11,
        },
    }


def delong_test(y_pred_proba_nn, y_pred_proba_xgb, y_true):
    """
    Comparison of ROC-AUC between NN and XGBoost.

    Uses DeLong method via bootstrap approximation
    (scipy doesn't have native DeLong, so we use bootstrap CI overlap).
    """
    n_classes = y_pred_proba_nn.shape[1]
    y_true_onehot = np.eye(n_classes)[y_true]

    try:
        auc_nn = roc_auc_score(y_true_onehot, y_pred_proba_nn, multi_class="ovr", average="macro")
        auc_xgb = roc_auc_score(y_true_onehot, y_pred_proba_xgb, multi_class="ovr", average="macro")
    except Exception:
        auc_nn = roc_auc_score(y_true, y_pred_proba_nn, multi_class="ovr", average="macro")
        auc_xgb = roc_auc_score(y_true, y_pred_proba_xgb, multi_class="ovr", average="macro")

    auc_diff = auc_nn - auc_xgb

    rng = np.random.RandomState(RANDOM_SEED)
    n = len(y_true)
    n_boot = 1000
    diffs = []
    for _ in range(n_boot):
        idx = rng.choice(n, size=n, replace=True)
        try:
            a_nn = roc_auc_score(y_true_onehot[idx], y_pred_proba_nn[idx], multi_class="ovr", average="macro")
            a_xgb = roc_auc_score(y_true_onehot[idx], y_pred_proba_xgb[idx], multi_class="ovr", average="macro")
            diffs.append(a_nn - a_xgb)
        except Exception:
            continue

    diffs = np.array(diffs)
    ci_lower = float(np.percentile(diffs, 2.5))
    ci_upper = float(np.percentile(diffs, 97.5))

    significant = ci_lower > 0 or ci_upper < 0

    return {
        "auc_nn": round(float(auc_nn), 6),
        "auc_xgb": round(float(auc_xgb), 6),
        "auc_difference": round(float(auc_diff), 6),
        "ci_lower_95": round(ci_lower, 6),
        "ci_upper_95": round(ci_upper, 6),
        "significant": significant,
        "interpretation": (
            "Significant ROC-AUC difference (CI excludes 0)" if significant
            else "No significant ROC-AUC difference (CI includes 0)"
        ),
    }


def run_statistical_comparison(nn_predictions, nn_probabilities, X_test_raw, y_test,
                               nn_scaler, nn_label_encoder):
    """
    Full statistical comparison: XGBoost vs Neural Network.

    Args:
        nn_predictions:    NN predicted class indices.
        nn_probabilities:  NN predicted probabilities.
        X_test_raw:        Unscaled test features (for XGBoost).
        y_test:            True labels (integer-encoded).
        nn_scaler:         NN scaler (for consistency).
        nn_label_encoder:  NN label encoder (for class mapping).

    Returns:
        dict with wilcoxon, mcnemar, delong results.
    """
    xgb_model, xgb_le = load_xgboost_artifacts()
    X_test_xgb = X_test_raw[FEATURE_COLUMNS]
    y_pred_xgb = xgb_model.predict(X_test_xgb)
    y_proba_xgb = xgb_model.predict_proba(X_test_xgb)

    wilcoxon = wilcoxon_test(nn_probabilities, y_proba_xgb, y_test)
    mcnemar = mcnemar_test(nn_predictions, y_pred_xgb, y_test)
    delong = delong_test(nn_probabilities, y_proba_xgb, y_test)

    comparison_df = pd.DataFrame([
        {"test": "Wilcoxon signed-rank", "statistic": wilcoxon["statistic"],
         "p_value": wilcoxon["p_value"], "interpretation": wilcoxon["interpretation"]},
        {"test": "McNemar", "statistic": mcnemar["statistic"],
         "p_value": mcnemar["p_value"], "interpretation": mcnemar["interpretation"]},
        {"test": "DeLong (bootstrap)", "statistic": delong["auc_difference"],
         "p_value": None, "interpretation": delong["interpretation"]},
    ])

    return {
        "wilcoxon": wilcoxon,
        "mcnemar": mcnemar,
        "delong": delong,
        "xgb_accuracy": round(float(accuracy_score(y_test, y_pred_xgb)), 6),
        "xgb_f1_macro": round(float(f1_score(y_test, y_pred_xgb, average="macro", zero_division=0)), 6),
        "comparison_table": comparison_df,
    }
