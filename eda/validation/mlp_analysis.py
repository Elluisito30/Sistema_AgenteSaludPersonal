"""
Phase 3 — MLP Deep Analysis for Health AI.

Loads the pre-trained Keras MLP (obesity_mlp.h5) and provides:
  1. Architecture summary & parameter count
  2. Per-class precision / recall / F1 comparison: MLP vs XGBoost
  3. Prediction probability distributions (entropy analysis)
  4. Misclassification pattern analysis
  5. Training convergence diagnostics (if training history available)

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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    classification_report, confusion_matrix, log_loss,
    roc_auc_score,
)
from scipy.stats import entropy as sp_entropy

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


def prepare_features_original(X):
    """Full preprocessing pipeline (matches train_eval.py)."""
    from sklearn.preprocessing import LabelEncoder as LE, StandardScaler, OneHotEncoder
    from sklearn.compose import ColumnTransformer

    Xf = X.copy()
    Xf["BMI"] = Xf["Weight"] / (Xf["Height"] ** 2)

    binary_vars = ["Gender", "family_history_with_overweight", "FAVC", "SMOKE", "SCC"]
    binary_encoders = {}
    for col in binary_vars:
        le = LE()
        le.fit(Xf[col])
        binary_encoders[col] = le
        Xf[col] = le.transform(Xf[col])

    col_transformer = ColumnTransformer(
        transformers=[
            ("binary", "passthrough", binary_vars),
            ("cat", OneHotEncoder(sparse_output=False, drop="first",
                                  handle_unknown="ignore"),
             ["CAEC", "CALC", "MTRANS"]),
            ("num", StandardScaler(),
             ["Age", "Height", "Weight", "FCVC", "NCP", "CH2O", "FAF", "TUE"]),
        ],
        remainder="drop",
    )
    X_processed = col_transformer.fit_transform(Xf)
    return X_processed, col_transformer, binary_encoders


# ── 1. Architecture summary ──────────────────────────────────────────────────

def architecture_summary():
    try:
        import tensorflow as tf
        mlp_path = os.path.join(MODELS_DIR, "obesity_mlp.h5")
        model = tf.keras.models.load_model(mlp_path, compile=False)
        print(f"\n  Model file: {mlp_path}")
        print(f"  Layers: {len(model.layers)}")
        total_params = model.count_params()
        print(f"  Total parameters: {total_params:,}")
        print(f"\n  Layer summary:")
        for layer in model.layers:
            cfg = layer.get_config()
            w = layer.get_weights()
            n_params = sum(np.prod(wi.shape) for wi in w) if w else 0
            out_dim = cfg.get("units", "?")
            print(f"    {layer.name:20s}  {layer.__class__.__name__:20s}  "
                  f"output={str(out_dim):6s}  params={n_params:,}")
        return True
    except Exception as e:
        print(f"  ⚠ Could not load MLP: {e}")
        return False


# ── 2. Per-class comparison ──────────────────────────────────────────────────

def per_class_comparison(mlp_preds, mlp_probas, xgb_preds, xgb_probas,
                         y_true, classes):
    rows = []
    for i, c in enumerate(classes):
        mask = y_true == i
        n = mask.sum()
        mlp_correct = (mlp_preds[mask] == i).mean()
        xgb_correct = (xgb_preds[mask] == i).mean()

        mlp_conf = mlp_probas[mask, i].mean() if mlp_probas is not None else np.nan
        xgb_conf = xgb_probas[mask, i].mean() if xgb_probas is not None else np.nan

        rows.append({
            "class": c,
            "n_samples": int(n),
            "mlp_accuracy": round(mlp_correct, 6),
            "xgb_accuracy": round(xgb_correct, 6),
            "accuracy_diff": round(mlp_correct - xgb_correct, 6),
            "mlp_mean_confidence": round(mlp_conf, 6),
            "xgb_mean_confidence": round(xgb_conf, 6),
        })
    return pd.DataFrame(rows)


# ── 3. Prediction entropy analysis ───────────────────────────────────────────

def entropy_analysis(probas, y_true, correct_mask, label):
    ent = sp_entropy(probas.T)
    rows = []
    for group, mask_val in [("correct", correct_mask), ("incorrect", ~correct_mask)]:
        sub = ent[mask_val]
        if len(sub) == 0:
            continue
        rows.append({
            "model": label,
            "group": group,
            "n_samples": int(len(sub)),
            "mean_entropy": round(float(np.mean(sub)), 6),
            "std_entropy":  round(float(np.std(sub)), 6),
            "median_entropy": round(float(np.median(sub)), 6),
        })
    return pd.DataFrame(rows)


# ── 4. Misclassification patterns ────────────────────────────────────────────

def misclassification_patterns(mlp_preds, xgb_preds, y_true, classes, n_top=5):
    """Find classes where MLP and XGBoost disagree the most."""
    disagree = mlp_preds != xgb_preds
    n_disagree = disagree.sum()
    total = len(y_true)
    agree_rate = 1 - n_disagree / total

    rows = []
    for i, c in enumerate(classes):
        mask = disagree & (y_true == i)
        count = mask.sum()
        if count == 0:
            continue
        mlp_wrong = (mlp_preds[mask] != i).sum()
        xgb_wrong = (xgb_preds[mask] != i).sum()
        rows.append({
            "true_class": c,
            "n_disagreements": int(count),
            "mlp_wrong_when_disagree": int(mlp_wrong),
            "xgb_wrong_when_disagree": int(xgb_wrong),
        })
    df = pd.DataFrame(rows).sort_values("n_disagreements", ascending=False).head(n_top)
    return agree_rate, df


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 78)
    print("PHASE 3 — MLP Deep Analysis")
    print("=" * 78)

    # Load data
    X_raw, y_raw = load_ucirepo_data()
    y = y_raw.iloc[:, 0]
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_

    X_proc, col_transformer, binary_encoders = prepare_features_original(X_raw)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_proc, y_enc, test_size=0.15, stratify=y_enc, random_state=SEED
    )
    _, X_te_raw, _, _ = train_test_split(
        X_raw, y_enc, test_size=0.15, stratify=y_enc, random_state=SEED
    )

    # ── 1. Architecture ──
    print(f"\n{'─' * 78}")
    print("[1/5] MLP Architecture Summary")
    print(f"{'─' * 78}")
    mlp_ok = architecture_summary()

    # ── 2. Load models & predict ──
    print(f"\n{'─' * 78}")
    print("[2/5] Model predictions on hold-out test set")
    print(f"{'─' * 78}")

    # MLP
    mlp_probas = None
    mlp_preds = None
    if mlp_ok:
        import tensorflow as tf
        mlp = tf.keras.models.load_model(
            os.path.join(MODELS_DIR, "obesity_mlp.h5"), compile=False
        )
        mlp_probas = mlp.predict(X_te, verbose=0)
        mlp_preds = mlp_probas.argmax(axis=-1)
        mlp_acc = accuracy_score(y_te, mlp_preds)
        mlp_f1  = f1_score(y_te, mlp_preds, average="macro")
        print(f"  MLP   — accuracy={mlp_acc:.4f}  f1_macro={mlp_f1:.4f}")

    # XGBoost (load from saved JSON — the original 23F model)
    xgb_m = xgb.XGBClassifier()
    xgb_m.load_model(os.path.join(MODELS_DIR, "xgb.json"))
    xgb_probas = xgb_m.predict_proba(X_te)
    xgb_preds = xgb_m.predict(X_te)
    xgb_acc = accuracy_score(y_te, xgb_preds)
    xgb_f1  = f1_score(y_te, xgb_preds, average="macro")
    print(f"  XGB   — accuracy={xgb_acc:.4f}  f1_macro={xgb_f1:.4f}")

    # ── 3. Per-class comparison ──
    print(f"\n{'─' * 78}")
    print("[3/5] Per-class accuracy: MLP vs XGBoost")
    print(f"{'─' * 78}")
    if mlp_ok:
        df_class = per_class_comparison(mlp_preds, mlp_probas, xgb_preds, xgb_probas,
                                        y_te, classes)
        for _, r in df_class.iterrows():
            better = "MLP" if r["accuracy_diff"] > 0 else "XGB" if r["accuracy_diff"] < 0 else "="
            print(f"  {r['class']:25s}  n={r['n_samples']:3d}  "
                  f"MLP={r['mlp_accuracy']:.4f}  XGB={r['xgb_accuracy']:.4f}  "
                  f"Δ={r['accuracy_diff']:+.4f}  ({better})")
    else:
        df_class = pd.DataFrame()

    # ── 4. Entropy analysis ──
    print(f"\n{'─' * 78}")
    print("[4/5] Prediction entropy (confidence proxy)")
    print(f"{'─' * 78}")
    all_entropy = []
    if mlp_ok:
        mlp_correct = mlp_preds == y_te
        e_mlp = entropy_analysis(mlp_probas, y_te, mlp_correct, "MLP")
        all_entropy.append(e_mlp)
        for _, r in e_mlp.iterrows():
            print(f"  MLP   {r['group']:10s}  n={r['n_samples']:4d}  "
                  f"entropy={r['mean_entropy']:.4f}±{r['std_entropy']:.4f}")

    xgb_correct = xgb_preds == y_te
    e_xgb = entropy_analysis(xgb_probas, y_te, xgb_correct, "XGBoost")
    all_entropy.append(e_xgb)
    for _, r in e_xgb.iterrows():
        print(f"  XGB   {r['group']:10s}  n={r['n_samples']:4d}  "
              f"entropy={r['mean_entropy']:.4f}±{r['std_entropy']:.4f}")

    df_entropy = pd.concat(all_entropy, ignore_index=True) if all_entropy else pd.DataFrame()

    # ── 5. Misclassification patterns ──
    print(f"\n{'─' * 78}")
    print("[5/5] Misclassification pattern: MLP vs XGBoost disagreements")
    print(f"{'─' * 78}")
    if mlp_ok:
        agree_rate, df_miscl = misclassification_patterns(mlp_preds, xgb_preds, y_te, classes)
        print(f"  Overall agreement rate: {agree_rate:.4f} ({int(agree_rate*len(y_te))}/{len(y_te)})")
        print(f"\n  Top classes where models disagree:")
        for _, r in df_miscl.iterrows():
            print(f"    {r['true_class']:25s}  n_disagree={r['n_disagreements']:3d}  "
                  f"mlp_wrong={r['mlp_wrong_when_disagree']}  "
                  f"xgb_wrong={r['xgb_wrong_when_disagree']}")
    else:
        df_miscl = pd.DataFrame()
        agree_rate = np.nan

    # ── Summary metrics ──
    print(f"\n{'─' * 78}")
    print("SUMMARY")
    print(f"{'─' * 78}")
    summary = {
        "mlp_accuracy": round(accuracy_score(y_te, mlp_preds), 6) if mlp_ok else np.nan,
        "xgb_accuracy": round(xgb_acc, 6),
        "mlp_f1_macro": round(f1_score(y_te, mlp_preds, average="macro"), 6) if mlp_ok else np.nan,
        "xgb_f1_macro": round(xgb_f1, 6),
        "mlp_xgb_agreement": round(agree_rate, 6) if not np.isnan(agree_rate) else np.nan,
    }
    for k, v in summary.items():
        print(f"  {k:25s}  {v}")

    # Save
    with pd.ExcelWriter(os.path.join(RESULTS_DIR, "mlp_analysis_results.xlsx"),
                        engine="openpyxl") as writer:
        if not df_class.empty:
            df_class.to_excel(writer, sheet_name="per_class", index=False)
        if not df_entropy.empty:
            df_entropy.to_excel(writer, sheet_name="entropy", index=False)
        if not df_miscl.empty:
            df_miscl.to_excel(writer, sheet_name="misclassifications", index=False)
        pd.DataFrame([summary]).to_excel(writer, sheet_name="summary", index=False)

    for name, df in [("per_class", df_class), ("entropy", df_entropy),
                     ("misclassifications", df_miscl)]:
        if not df.empty:
            df.to_csv(os.path.join(RESULTS_DIR, f"mlp_{name}.csv"), index=False)

    print(f"\n✓ Saved → {RESULTS_DIR}/mlp_analysis_results.xlsx")
    print(f"✓ Saved → {RESULTS_DIR}/mlp_*.csv")
    return summary


if __name__ == "__main__":
    main()
