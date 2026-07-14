"""
Phase 3 — Wilcoxon Signed-Rank & Paired-t Tests for Model Comparison.

Uses the cross-validation fold scores stored in eda/models/cv_results.csv
to perform pairwise statistical significance tests between all four models
(Logistic Regression, Random Forest, XGBoost, MLP).

Additionally runs Wilcoxon tests on the 11F vs 6F XGBoost models by
re-running 10×5 CV on both feature sets and comparing fold-level metrics.

Reuses: eda/models/cv_results.csv, UCI Obesity dataset.
No backend / frontend / Docker modifications.
"""

import warnings
warnings.filterwarnings("ignore")

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, ttest_rel
from sklearn.preprocessing import LabelEncoder
from itertools import combinations

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "models")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

SEED = 42


# ── Helpers ───────────────────────────────────────────────────────────────────

def interpret_wilcoxon(stat, p, alpha=0.05):
    if p < alpha:
        return "significant"
    return "not significant"


def effect_size_r(stat, n):
    """r = Z / sqrt(N) — common effect size for Wilcoxon."""
    from scipy.stats import norm
    z = norm.ppf(1 - p / 2) if p > 0 else 0
    return z / np.sqrt(n) if n > 0 else 0.0


# ── Part 1: Pairwise tests on existing CV results ────────────────────────────

def pairwise_from_cv_results():
    cv = pd.read_csv(os.path.join(MODELS_DIR, "cv_results.csv"))
    metrics = ["accuracy", "balanced_accuracy", "f1_macro", "roc_auc_ovr"]
    models = cv["model"].unique()

    rows = []
    for metric in metrics:
        for m1, m2 in combinations(models, 2):
            s1 = cv[cv["model"] == m1][metric].dropna().values
            s2 = cv[cv["model"] == m2][metric].dropna().values
            n = min(len(s1), len(s2))
            s1, s2 = s1[:n], s2[:n]

            if n < 2 or np.all(s1 == s2):
                continue

            # Wilcoxon signed-rank (paired, two-sided)
            try:
                stat_w, p_w = wilcoxon(s1, s2, alternative="two-sided")
            except ValueError:
                stat_w, p_w = np.nan, np.nan

            # Paired t-test
            stat_t, p_t = ttest_rel(s1, s2)

            rows.append({
                "metric": metric,
                "model_A": m1,
                "model_B": m2,
                "n_folds": n,
                "mean_A": round(np.mean(s1), 6),
                "mean_B": round(np.mean(s2), 6),
                "mean_diff": round(np.mean(s1) - np.mean(s2), 6),
                "wilcoxon_stat": round(stat_w, 6) if not np.isnan(stat_w) else np.nan,
                "wilcoxon_p": round(p_w, 6) if not np.isnan(p_w) else np.nan,
                "wilcoxon_interpretation": interpret_wilcoxon(stat_w, p_w)
                                          if not np.isnan(p_w) else "N/A",
                "paired_t_stat": round(stat_t, 6),
                "paired_t_p": round(p_t, 6),
                "paired_t_interpretation": interpret_wilcoxon(stat_t, p_t),
            })

    return pd.DataFrame(rows)


# ── Part 2: 11F vs 6F head-to-head via fresh CV ─────────────────────────────

def head_to_head_11f_vs_6f():
    from ucimlrepo import fetch_ucirepo
    from sklearn.model_selection import RepeatedStratifiedKFold
    from sklearn.metrics import (
        accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score,
    )
    import xgboost as xgb

    obesity = fetch_ucirepo(id=544)
    X_raw = obesity.data.features
    y_raw = obesity.data.targets.iloc[:, 0]

    le = LabelEncoder()
    y_enc = le.fit_transform(y_raw)

    def feats_11(X):
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

    def feats_6(X):
        Xf = pd.DataFrame()
        Xf["Age"]    = X["Age"]
        Xf["Gender"] = X["Gender"].map({"male": 1, "female": 0})
        Xf["Height"] = X["Height"]
        Xf["Weight"] = X["Weight"]
        Xf["SMOKE"]  = X["SMOKE"].map({"yes": 1, "no": 0})
        Xf["FAF"]    = X["FAF"]
        return Xf

    rkf = RepeatedStratifiedKFold(n_splits=10, n_repeats=5, random_state=SEED)

    scores_11 = {m: [] for m in ["accuracy", "balanced_accuracy", "f1_macro", "roc_auc_ovr"]}
    scores_6  = {m: [] for m in ["accuracy", "balanced_accuracy", "f1_macro", "roc_auc_ovr"]}

    print("  Running 10×5 Repeated Stratified K-Fold for both feature sets ...")
    for fold_i, (tr_idx, va_idx) in enumerate(rkf.split(X_raw, y_enc)):
        Xtr, Xva = X_raw.iloc[tr_idx], X_raw.iloc[va_idx]
        ytr, yva = y_enc[tr_idx], y_enc[va_idx]

        for feat_fn, sc in [(feats_11, scores_11), (feats_6, scores_6)]:
            Xtr_f = feat_fn(Xtr)
            Xva_f = feat_fn(Xva)
            m = xgb.XGBClassifier(
                n_estimators=100, objective="multi:softprob",
                num_class=len(np.unique(y_enc)),
                random_state=SEED, verbosity=0,
            )
            m.fit(Xtr_f, ytr)
            yp = m.predict(Xva_f)
            ypr = m.predict_proba(Xva_f)
            sc["accuracy"].append(accuracy_score(yva, yp))
            sc["balanced_accuracy"].append(balanced_accuracy_score(yva, yp))
            sc["f1_macro"].append(f1_score(yva, yp, average="macro"))
            try:
                sc["roc_auc_ovr"].append(roc_auc_score(yva, ypr, multi_class="ovr"))
            except Exception:
                sc["roc_auc_ovr"].append(np.nan)

    rows = []
    for metric in ["accuracy", "balanced_accuracy", "f1_macro", "roc_auc_ovr"]:
        s11 = np.array(scores_11[metric])
        s6  = np.array(scores_6[metric])
        valid = ~(np.isnan(s11) | np.isnan(s6))
        s11, s6 = s11[valid], s6[valid]
        n = len(s11)

        try:
            stat_w, p_w = wilcoxon(s11, s6, alternative="two-sided")
        except ValueError:
            stat_w, p_w = np.nan, np.nan

        stat_t, p_t = ttest_rel(s11, s6)

        rows.append({
            "metric": metric,
            "model_A": "XGBoost_11F",
            "model_B": "XGBoost_6F",
            "n_folds": n,
            "mean_A": round(np.mean(s11), 6),
            "mean_B": round(np.mean(s6), 6),
            "mean_diff": round(np.mean(s11) - np.mean(s6), 6),
            "wilcoxon_stat": round(stat_w, 6) if not np.isnan(stat_w) else np.nan,
            "wilcoxon_p": round(p_w, 6) if not np.isnan(p_w) else np.nan,
            "wilcoxon_interpretation": interpret_wilcoxon(stat_w, p_w)
                                      if not np.isnan(p_w) else "N/A",
            "paired_t_stat": round(stat_t, 6),
            "paired_t_p": round(p_t, 6),
            "paired_t_interpretation": interpret_wilcoxon(stat_t, p_t),
        })

    return pd.DataFrame(rows)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 78)
    print("PHASE 3 — Wilcoxon Signed-Rank & Paired-t Tests")
    print("=" * 78)

    print("\n[1/2] Pairwise tests on existing CV fold scores ...")
    print("      (Note: cv_results.csv has only 2 folds per model — Wilcoxon")
    print("       requires n≥2 but results should be interpreted cautiously)")
    df_existing = pairwise_from_cv_results()
    print(f"      {len(df_existing)} comparisons generated")

    print("\n[2/2] Head-to-head: XGBoost 11F vs 6F (fresh 10×5 CV) ...")
    df_h2h = head_to_head_11f_vs_6f()
    print(f"      {len(df_h2h)} comparisons generated")

    combined = pd.concat([df_existing, df_h2h], ignore_index=True)

    # Pretty print summary
    print(f"\n{'─' * 78}")
    print("SIGNIFICANT PAIRWISE DIFFERENCES (Wilcoxon p < 0.05)")
    print(f"{'─' * 78}")
    sig = combined[combined["wilcoxon_interpretation"] == "significant"]
    if sig.empty:
        print("  None — no statistically significant pairwise differences found.")
    else:
        for _, r in sig.iterrows():
            direction = "A > B" if r["mean_diff"] > 0 else "A < B"
            print(f"  {r['metric']:22s}  {r['model_A']} vs {r['model_B']:<22s}  "
                  f"p={r['wilcoxon_p']:.4f}  ({direction})")

    print(f"\n{'─' * 78}")
    print("ALL COMPARISONS")
    print(f"{'─' * 78}")
    for _, r in combined.iterrows():
        sig_mark = " *" if r["wilcoxon_interpretation"] == "significant" else ""
        print(f"  {r['metric']:22s}  {r['model_A']:16s} vs {r['model_B']:16s}  "
              f"Δ={r['mean_diff']:+.4f}  W-p={r['wilcoxon_p']:.4f}  "
              f"t-p={r['paired_t_p']:.4f}{sig_mark}")

    out_path = os.path.join(RESULTS_DIR, "wilcoxon_results.csv")
    combined.to_csv(out_path, index=False)
    print(f"\n✓ Saved → {out_path}")
    return combined


if __name__ == "__main__":
    main()
