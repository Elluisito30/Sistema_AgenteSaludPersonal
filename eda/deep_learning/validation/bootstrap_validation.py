"""
Bootstrap validation for confidence intervals.

Computes 95% bootstrap CIs for Accuracy, F1-macro, and ROC-AUC OvR.
"""

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score


def bootstrap_metric(y_true, y_pred, y_pred_proba, metric_fn, n_bootstrap=1000, seed=42):
    """
    Compute bootstrap confidence interval for a given metric.

    Args:
        y_true:        True labels.
        y_pred:        Predicted labels.
        y_pred_proba:  Predicted probabilities.
        metric_fn:     Function(y_true, y_pred, y_pred_proba) -> float.
        n_bootstrap:   Number of bootstrap iterations.
        seed:          Random seed.

    Returns:
        dict with point estimate, ci_lower, ci_upper, std.
    """
    rng = np.random.RandomState(seed)
    n = len(y_true)
    scores = []

    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        y_t = y_true[idx]
        y_p = y_pred[idx]
        y_pp = y_pred_proba[idx]

        try:
            score = metric_fn(y_t, y_p, y_pp)
            scores.append(score)
        except Exception:
            continue

    scores = np.array(scores)
    point_estimate = metric_fn(y_true, y_pred, y_pred_proba)
    ci_lower = float(np.percentile(scores, 2.5))
    ci_upper = float(np.percentile(scores, 97.5))
    std = float(np.std(scores))

    return {
        "point_estimate": round(float(point_estimate), 6),
        "ci_lower": round(ci_lower, 6),
        "ci_upper": round(ci_upper, 6),
        "std": round(std, 6),
        "n_bootstrap": len(scores),
    }


def accuracy_metric(y_true, y_pred, y_pred_proba):
    return accuracy_score(y_true, y_pred)


def f1_macro_metric(y_true, y_pred, y_pred_proba):
    return f1_score(y_true, y_pred, average="macro", zero_division=0)


def roc_auc_macro_metric(y_true, y_pred, y_pred_proba):
    return roc_auc_score(y_true, y_pred_proba, multi_class="ovr", average="macro")


def run_bootstrap_validation(y_true, y_pred, y_pred_proba, n_bootstrap=1000, seed=42):
    """
    Run bootstrap analysis for all three metrics.

    Returns:
        dict with accuracy, f1_macro, roc_auc_ovr bootstrap results.
    """
    accuracy = bootstrap_metric(y_true, y_pred, y_pred_proba, accuracy_metric, n_bootstrap, seed)
    f1_macro = bootstrap_metric(y_true, y_pred, y_pred_proba, f1_macro_metric, n_bootstrap, seed)
    roc_auc = bootstrap_metric(y_true, y_pred, y_pred_proba, roc_auc_macro_metric, n_bootstrap, seed)

    return {
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "roc_auc_ovr": roc_auc,
        "n_bootstrap": n_bootstrap,
    }
