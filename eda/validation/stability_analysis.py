"""
Phase 3 — Model Stability & Agreement Analysis.

Evaluates how stable and consistent the Health AI models are:
  1. Prediction agreement between models (Cohen's Kappa, Jaccard)
  2. Class-level stability (per-class accuracy variance across CV folds)
  3. Confidence calibration (mean predicted probability vs actual accuracy)
  4. Sensitivity to feature perturbation (noise injection test)

Reuses: eda/models/ artifacts, UCI Obesity dataset (id=544).
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
from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score, cohen_kappa_score,
    confusion_matrix,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "models")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

SEED = 42


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
    Xf = Xf.fillna(0)
    return Xf


def prepare_features_6(X):
    Xf = pd.DataFrame()
    Xf["Age"]    = X["Age"]
    Xf["Gender"] = X["Gender"].map({"male": 1, "female": 0})
    Xf["Height"] = X["Height"]
    Xf["Weight"] = X["Weight"]
    Xf["SMOKE"]  = X["SMOKE"].map({"yes": 1, "no": 0})
    Xf["FAF"]    = X["FAF"]
    Xf = Xf.fillna(0)
    return Xf


# ── Analysis 1: Inter-model prediction agreement ─────────────────────────────

def prediction_agreement(X_train, y_train, X_test, y_test, classes):
    """Cohen's Kappa and Jaccard similarity between all model pairs."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier

    models = {
        "Logistic Regression": LogisticRegression(max_iter=500, random_state=SEED),
        "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=SEED),
        "XGBoost_11F":         xgb.XGBClassifier(
            n_estimators=100, objective="multi:softprob",
            num_class=len(classes), random_state=SEED, verbosity=0),
    }

    preds = {}
    for name, m in models.items():
        m.fit(X_train, y_train)
        preds[name] = m.predict(X_test)

    from itertools import combinations
    rows = []
    for n1, n2 in combinations(models.keys(), 2):
        kappa = cohen_kappa_score(preds[n1], preds[n2])
        agree = np.mean(preds[n1] == preds[n2])
        rows.append({
            "comparison": f"{n1} vs {n2}",
            "cohen_kappa": round(kappa, 6),
            "agreement_rate": round(agree, 6),
            "n_samples": len(y_test),
        })
    return pd.DataFrame(rows)


# ── Analysis 2: Class-level stability across CV folds ─────────────────────────

def class_stability(X, y, classes, n_splits=10, n_repeats=3, seed=SEED):
    """Per-class accuracy variance across CV folds (lower = more stable)."""
    rkf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    class_accs = {c: [] for c in classes}

    for tr_idx, va_idx in rkf.split(X, y):
        Xtr, Xva = X.iloc[tr_idx], X.iloc[va_idx]
        ytr, yva = y[tr_idx], y[va_idx]

        m = xgb.XGBClassifier(
            n_estimators=100, objective="multi:softprob",
            num_class=len(classes), random_state=seed, verbosity=0,
        )
        m.fit(Xtr, ytr)
        yp = m.predict(Xva)

        cm = confusion_matrix(yva, yp, labels=list(range(len(classes))))
        for i, c in enumerate(classes):
            total = cm[i].sum()
            class_accs[c].append(cm[i, i] / total if total > 0 else 0.0)

    rows = []
    for c in classes:
        accs = np.array(class_accs[c])
        rows.append({
            "class": c,
            "mean_accuracy": round(np.mean(accs), 6),
            "std_accuracy":  round(np.std(accs), 6),
            "min_accuracy":  round(np.min(accs), 6),
            "max_accuracy":  round(np.max(accs), 6),
            "cv_folds": len(accs),
            "stability_cv": round(np.std(accs) / np.mean(accs), 6) if np.mean(accs) > 0 else np.nan,
        })
    return pd.DataFrame(rows)


# ── Analysis 3: Confidence calibration ────────────────────────────────────────

def confidence_calibration(X_train, y_train, X_test, y_test, n_bins=10):
    """Binned calibration: mean predicted confidence vs observed accuracy."""
    m = xgb.XGBClassifier(
        n_estimators=100, objective="multi:softprob",
        num_class=len(np.unique(y_train)), random_state=SEED, verbosity=0,
    )
    m.fit(X_train, y_train)
    ypred = m.predict(X_test)
    yprob = m.predict_proba(X_test)

    confidences = yprob.max(axis=1)
    correct = (ypred == y_test).astype(float)

    bins = np.linspace(0, 1, n_bins + 1)
    rows = []
    for i in range(n_bins):
        mask = (confidences >= bins[i]) & (confidences < bins[i + 1])
        n = mask.sum()
        if n == 0:
            continue
        rows.append({
            "bin_lower": round(bins[i], 2),
            "bin_upper": round(bins[i + 1], 2),
            "mean_confidence": round(float(np.mean(confidences[mask])), 6),
            "accuracy": round(float(np.mean(correct[mask])), 6),
            "n_samples": int(n),
        })
    return pd.DataFrame(rows)


# ── Analysis 4: Feature perturbation sensitivity ──────────────────────────────

def perturbation_sensitivity(X, y, classes, noise_levels=(0.01, 0.05, 0.10, 0.20),
                             n_repeats=10, seed=SEED):
    """Accuracy degradation under Gaussian noise injection to numeric features."""
    rng = np.random.RandomState(seed)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.15, stratify=y, random_state=seed)

    m = xgb.XGBClassifier(
        n_estimators=100, objective="multi:softprob",
        num_class=len(classes), random_state=seed, verbosity=0,
    )
    m.fit(Xtr, ytr)
    baseline_acc = accuracy_score(yte, m.predict(Xte))

    stds = Xtr.std().values

    rows = [{"noise_std": 0.0, "mean_accuracy": baseline_acc, "std_accuracy": 0.0,
             "accuracy_drop": 0.0}]
    for nl in noise_levels:
        accs = []
        for _ in range(n_repeats):
            noise = rng.normal(0, nl, Xte.shape) * stds
            X_noisy = Xte.values + noise
            accs.append(accuracy_score(yte, m.predict(X_noisy)))
        mean_acc = np.mean(accs)
        rows.append({
            "noise_std": nl,
            "mean_accuracy": round(mean_acc, 6),
            "std_accuracy": round(np.std(accs), 6),
            "accuracy_drop": round(baseline_acc - mean_acc, 6),
        })
    return pd.DataFrame(rows)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 78)
    print("PHASE 3 — Model Stability & Agreement Analysis")
    print("=" * 78)

    X_raw, y_raw = load_ucirepo_data()
    y = y_raw.iloc[:, 0]
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_

    X11 = prepare_features_11(X_raw)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X11, y_enc, test_size=0.15, stratify=y_enc, random_state=SEED
    )

    # 1. Prediction agreement
    print(f"\n{'─' * 78}")
    print("[1/4] Inter-model prediction agreement (test set)")
    print(f"{'─' * 78}")
    df_agree = prediction_agreement(X_tr, y_tr, X_te, y_te, classes)
    for _, r in df_agree.iterrows():
        print(f"  {r['comparison']:45s}  κ={r['cohen_kappa']:.4f}  "
              f"agree={r['agreement_rate']:.4f}")

    # 2. Class-level stability
    print(f"\n{'─' * 78}")
    print("[2/4] Class-level stability across 3×10 CV folds")
    print(f"{'─' * 78}")
    df_class = class_stability(X11, y_enc, classes)
    for _, r in df_class.iterrows():
        print(f"  {r['class']:25s}  acc={r['mean_accuracy']:.4f}±{r['std_accuracy']:.4f}  "
              f"range=[{r['min_accuracy']:.4f}, {r['max_accuracy']:.4f}]  "
              f"CV={r['stability_cv']:.4f}")

    # 3. Confidence calibration
    print(f"\n{'─' * 78}")
    print("[3/4] Confidence calibration (XGBoost 11F)")
    print(f"{'─' * 78}")
    df_cal = confidence_calibration(X_tr, y_tr, X_te, y_te)
    for _, r in df_cal.iterrows():
        gap = abs(r["mean_confidence"] - r["accuracy"])
        print(f"  [{r['bin_lower']:.1f}, {r['bin_upper']:.1f})  "
              f"conf={r['mean_confidence']:.4f}  acc={r['accuracy']:.4f}  "
              f"gap={gap:.4f}  n={r['n_samples']}")

    # 4. Perturbation sensitivity
    print(f"\n{'─' * 78}")
    print("[4/4] Feature perturbation sensitivity")
    print(f"{'─' * 78}")
    df_pert = perturbation_sensitivity(X11, y_enc, classes)
    for _, r in df_pert.iterrows():
        print(f"  noise_σ={r['noise_std']:.2f}  acc={r['mean_accuracy']:.4f}±"
              f"{r['std_accuracy']:.4f}  drop={r['accuracy_drop']:.4f}")

    # Save all
    with pd.ExcelWriter(os.path.join(RESULTS_DIR, "stability_results.xlsx"),
                        engine="openpyxl") as writer:
        df_agree.to_excel(writer, sheet_name="agreement", index=False)
        df_class.to_excel(writer, sheet_name="class_stability", index=False)
        df_cal.to_excel(writer, sheet_name="calibration", index=False)
        df_pert.to_excel(writer, sheet_name="perturbation", index=False)

    # Also save individual CSVs
    for name, df in [("agreement", df_agree), ("class_stability", df_class),
                     ("calibration", df_cal), ("perturbation", df_pert)]:
        df.to_csv(os.path.join(RESULTS_DIR, f"stability_{name}.csv"), index=False)

    print(f"\n✓ Saved → {RESULTS_DIR}/stability_*.csv + stability_results.xlsx")
    return df_agree, df_class, df_cal, df_pert


if __name__ == "__main__":
    main()
