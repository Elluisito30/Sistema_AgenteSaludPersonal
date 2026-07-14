"""
Train XGBoost model with 11 features (6 existing + 4 new + BMI).

Features:
- Age, Gender, Height, Weight, SMOKE, FAF (existing 6)
- family_history, FAVC, FCVC, CH2O (new 4)
- BMI (computed)
"""

import warnings
warnings.filterwarnings('ignore')

import os
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    roc_auc_score, classification_report
)
from ucimlrepo import fetch_ucirepo

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'models')

SEED = 42


def load_data():
    obesity = fetch_ucirepo(id=544)
    X = obesity.data.features
    y = obesity.data.targets
    return X, y


def prepare_features_11(X):
    """Prepare 11 features available in health_profiles."""
    X_avail = pd.DataFrame()
    X_avail['Age'] = X['Age']
    X_avail['Gender'] = X['Gender'].map({'male': 1, 'female': 0})
    X_avail['Height'] = X['Height']
    X_avail['Weight'] = X['Weight']
    X_avail['SMOKE'] = X['SMOKE'].map({'yes': 1, 'no': 0})
    X_avail['FAF'] = X['FAF']
    X_avail['BMI'] = X['Weight'] / (X['Height'] ** 2)
    X_avail['family_history'] = X['family_history_with_overweight'].map({'yes': 1, 'no': 0})
    X_avail['FAVC'] = X['FAVC'].map({'yes': 1, 'no': 0})
    X_avail['FCVC'] = X['FCVC']
    X_avail['CH2O'] = X['CH2O']
    return X_avail


def main():
    print("=" * 80)
    print("XGBoost with 11 features (6 existing + 4 new + BMI)")
    print("=" * 80)

    X_raw, y_raw = load_data()
    y = y_raw.iloc[:, 0]

    le_target = LabelEncoder()
    y_encoded = le_target.fit_transform(y)

    X_avail = prepare_features_11(X_raw)
    print(f"\nFeatures ({X_avail.shape[1]}): {list(X_avail.columns)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X_avail, y_encoded, test_size=0.15, stratify=y_encoded, random_state=SEED
    )

    model = xgb.XGBClassifier(
        n_estimators=100,
        objective='multi:softprob',
        num_class=7,
        random_state=SEED,
        verbosity=0
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro')
    roc_auc = roc_auc_score(y_test, y_proba, multi_class='ovr')

    print(f"\n--- Hold-out Test (317 samples) ---")
    print(f"Accuracy:          {acc:.4f}")
    print(f"Balanced Accuracy: {bal_acc:.4f}")
    print(f"F1 Macro:          {f1:.4f}")
    print(f"ROC-AUC OvR:       {roc_auc:.4f}")
    print()
    print(classification_report(y_test, y_pred, target_names=le_target.classes_))

    # Cross-validation
    print("--- 10x5 Repeated Stratified K-Fold ---")
    rkf = RepeatedStratifiedKFold(n_splits=10, n_repeats=5, random_state=SEED)
    acc_scores, bal_scores, f1_scores, auc_scores = [], [], [], []
    for train_idx, val_idx in rkf.split(X_avail, y_encoded):
        X_tr, X_val = X_avail.iloc[train_idx], X_avail.iloc[val_idx]
        y_tr, y_val = y_encoded[train_idx], y_encoded[val_idx]
        m = xgb.XGBClassifier(n_estimators=100, objective='multi:softprob', num_class=7, random_state=SEED, verbosity=0)
        m.fit(X_tr, y_tr)
        yp = m.predict(X_val)
        ypr = m.predict_proba(X_val)
        acc_scores.append(accuracy_score(y_val, yp))
        bal_scores.append(balanced_accuracy_score(y_val, yp))
        f1_scores.append(f1_score(y_val, yp, average='macro'))
        try:
            auc_scores.append(roc_auc_score(y_val, ypr, multi_class='ovr'))
        except:
            auc_scores.append(np.nan)

    print(f"Accuracy:          {np.mean(acc_scores):.4f} +/- {np.std(acc_scores):.4f}")
    print(f"Balanced Accuracy: {np.mean(bal_scores):.4f} +/- {np.std(bal_scores):.4f}")
    print(f"F1 Macro:          {np.mean(f1_scores):.4f} +/- {np.std(f1_scores):.4f}")
    print(f"ROC-AUC OvR:       {np.nanmean(auc_scores):.4f} +/- {np.nanstd(auc_scores):.4f}")

    # Save model
    model.save_model(os.path.join(MODELS_DIR, 'xgb_11f.bin'))
    joblib.dump(le_target, os.path.join(MODELS_DIR, 'le_target_11f.pkl'))
    print(f"\nSaved: xgb_11f.bin, le_target_11f.pkl")

    # Feature importance
    print("\n--- Feature Importance ---")
    for name, imp in sorted(zip(X_avail.columns, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {name:<20s} {imp:.4f}")


if __name__ == "__main__":
    main()
