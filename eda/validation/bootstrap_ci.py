"""
Phase 3 — Bootstrap Confidence Intervals for Health AI Models.

Re-trains XGBoost (11F and 6F) on B bootstrap resamples of the training data,
evaluates each on the held-out test set, and computes percentile 95% CIs for
accuracy, balanced accuracy, F1-macro, and ROC-AUC OvR.

Reuses: UCI Obesity dataset (id=544), eda/models/ artifacts.
No backend / frontend / Docker modifications.
"""

import warnings
warnings.filterwarnings("ignore")

import os
import sys
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "models")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

SEED = 42
N_BOOTSTRAP = 100
ALPHA = 0.05


# ── Data helpers ──────────────────────────────────────────────────────────────

def load_ucirepo_data():
    from ucimlrepo import fetch_ucirepo
    obesity = fetch_ucirepo(id=544)
    return obesity.data.features, obesity.data.targets


def prepare_features_11(X):
    Xf = pd.DataFrame()
    Xf["Age"]  = X["Age"]
    Xf["Gender"] = X["Gender"].map({"male": 1, "female": 0})
    Xf["Height"] = X["Height"]
    Xf["Weight"] = X["Weight"]
    Xf["SMOKE"]  = X["SMOKE"].map({"yes": 1, "no": 0})
    Xf["FAF"]   = X["FAF"]
    Xf["BMI"]   = X["Weight"] / (X["Height"] ** 2)
    Xf["family_history"] = X["family_history_with_overweight"].map({"yes": 1, "no": 0})
    Xf["FAVC"]  = X["FAVC"].map({"yes": 1, "no": 0})
    Xf["FCVC"]  = X["FCVC"]
    Xf["CH2O"]  = X["CH2O"]
    return Xf


def prepare_features_6(X):
    Xf = pd.DataFrame()
    Xf["Age"]    = X["Age"]
    Xf["Gender"] = X["Gender"].map({"male": 1, "female": 0})
    Xf["Height"] = X["Height"]
    Xf["Weight"] = X["Weight"]
    Xf["SMOKE"]  = X["SMOKE"].map({"yes": 1, "no": 0})
    Xf["FAF"]    = X["FAF"]
    return Xf


def compute_metrics(y_true, y_pred, y_proba):
    return {
        "accuracy":          accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "f1_macro":          f1_score(y_true, y_pred, average="macro"),
        "roc_auc_ovr":       roc_auc_score(y_true, y_proba, multi_class="ovr")
                             if y_proba is not None else np.nan,
    }


# ── Bootstrap engine ─────────────────────────────────────────────────────────

def bootstrap_ci(X_train, y_train, X_test, y_test,
                 n_boot=N_BOOTSTRAP, seed=SEED):
    rng = np.random.RandomState(seed)
    records = []

    for b in range(n_boot):
        idx = rng.choice(len(X_train), size=len(X_train), replace=True)
        X_b = X_train.iloc[idx]
        y_b = y_train[idx]

        m = xgb.XGBClassifier(
            n_estimators=100,
            objective="multi:softprob",
            num_class=len(np.unique(y_train)),
            random_state=seed + b,
            verbosity=0,
        )
        m.fit(X_b, y_b)
        yp = m.predict(X_test)
        ypr = m.predict_proba(X_test)
        metrics = compute_metrics(y_test, yp, ypr)
        metrics["bootstrap_sample"] = b
        records.append(metrics)

    return pd.DataFrame(records)


def ci_percentile(series, alpha=ALPHA):
    lo = np.percentile(series, 100 * alpha / 2)
    hi = np.percentile(series, 100 * (1 - alpha / 2))
    return lo, hi


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 78)
    print("PHASE 3 — Bootstrap Confidence Intervals (95%)")
    print("=" * 78)

    X_raw, y_raw = load_ucirepo_data()
    y = y_raw.iloc[:, 0]

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_raw, y_enc, test_size=0.15, stratify=y_enc, random_state=SEED
    )

    configs = {
        "XGBoost_11F": prepare_features_11,
        "XGBoost_6F":  prepare_features_6,
    }

    all_rows = []

    for label, feat_fn in configs.items():
        print(f"\n{'─' * 78}")
        print(f"  {label} — {N_BOOTSTRAP} bootstrap resamples")
        print(f"{'─' * 78}")

        Xtr_f = feat_fn(X_tr)
        Xte_f = feat_fn(X_te)

        df_boot = bootstrap_ci(Xtr_f, y_tr, Xte_f, y_te)

        for metric in ["accuracy", "balanced_accuracy", "f1_macro", "roc_auc_ovr"]:
            vals = df_boot[metric].values
            mean = np.mean(vals)
            std  = np.std(vals)
            lo, hi = ci_percentile(vals)
            print(f"  {metric:<22s}  mean={mean:.4f}  std={std:.4f}  "
                  f"CI95=[{lo:.4f}, {hi:.4f}]")
            all_rows.append({
                "model": label,
                "metric": metric,
                "mean": round(mean, 6),
                "std": round(std, 6),
                "ci95_lower": round(lo, 6),
                "ci95_upper": round(hi, 6),
                "n_bootstrap": N_BOOTSTRAP,
            })

    out = pd.DataFrame(all_rows)
    out_path = os.path.join(RESULTS_DIR, "bootstrap_ci_results.csv")
    out.to_csv(out_path, index=False)
    print(f"\n✓ Saved → {out_path}")
    return out


if __name__ == "__main__":
    main()
