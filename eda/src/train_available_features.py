"""
Train XGBoost model using only features available in health_profiles.

Available features:
- Age (numeric)
- Gender (binary: male/female)
- Height (numeric)
- Weight (numeric)
- SMOKE (binary: yes/no)
- FAF (numeric: 0-3, mapped from activity_level)

Features NOT available (10 features, 52.8% importance):
- family_history_with_overweight, FAVC, FCVC, NCP, CAEC, CH2O, SCC, TUE, CALC, MTRANS

Target: NObeyesdad (7 classes)
"""

import warnings
warnings.filterwarnings('ignore')

import os
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score, 
    roc_auc_score, confusion_matrix, classification_report
)
from ucimlrepo import fetch_ucirepo

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

SEED = 42


def load_data():
    """Load UCI Obesity dataset."""
    obesity = fetch_ucirepo(id=544)
    X = obesity.data.features
    y = obesity.data.targets
    return X, y


def prepare_features_available_only(X):
    """
    Prepare features available in health_profiles only.
    
    Maps:
    - Gender: male -> 1, female -> 0
    - SMOKE: yes -> 1, no -> 0
    - FAF: keep as-is (0-3 scale, mapped from activity_level)
    - Age, Height, Weight: keep as-is
    
    Returns: pd.DataFrame with 6 columns
    """
    X_avail = pd.DataFrame()
    X_avail['Age'] = X['Age']
    X_avail['Gender'] = X['Gender'].map({'male': 1, 'female': 0})
    X_avail['Height'] = X['Height']
    X_avail['Weight'] = X['Weight']
    X_avail['SMOKE'] = X['SMOKE'].map({'yes': 1, 'no': 0})
    X_avail['FAF'] = X['FAF']
    return X_avail


def prepare_features_original(X):
    """
    Prepare all features using original preprocessing pipeline.
    """
    X_orig = X.copy()
    X_orig['BMI'] = X_orig['Weight'] / (X_orig['Height'] ** 2)
    
    # Binary encoders
    binary_vars = ['Gender', 'family_history_with_overweight', 'FAVC', 'SMOKE', 'SCC']
    binary_encoders = {}
    for col in binary_vars:
        le = LabelEncoder()
        le.fit(X_orig[col])
        binary_encoders[col] = le
        X_orig[col] = le.transform(X_orig[col])
    
    # One-hot encode categorical
    X_orig = pd.get_dummies(X_orig, columns=['CAEC', 'CALC', 'MTRANS'], drop_first=True)
    
    # Keep only numeric columns
    feature_cols = [c for c in X_orig.columns if c != 'NObeyesdad']
    X_orig = X_orig[feature_cols]
    
    return X_orig, binary_encoders


def train_evaluate_model(X_train, X_test, y_train, y_test, model_name, seed=42):
    """Train XGBoost and evaluate on test set."""
    
    # Train
    model = xgb.XGBClassifier(
        n_estimators=100,
        objective='multi:softprob',
        num_class=7,
        random_state=seed,
        verbosity=0
    )
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Metrics
    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    
    try:
        roc_auc = roc_auc_score(y_test, y_proba, multi_class='ovr')
    except:
        roc_auc = np.nan
    
    return {
        'model_name': model_name,
        'accuracy': acc,
        'balanced_accuracy': bal_acc,
        'f1_macro': f1_macro,
        'roc_auc_ovr': roc_auc,
        'model': model
    }


def cross_validate_model(X, y, n_splits=10, n_repeats=5, seed=42):
    """Run repeated stratified k-fold cross-validation."""
    rkf = RepeatedStratifiedKFold(
        n_splits=n_splits, n_repeats=n_repeats, random_state=seed
    )
    
    acc_scores = []
    bal_acc_scores = []
    f1_scores = []
    auc_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(rkf.split(X, y)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            objective='multi:softprob',
            num_class=7,
            random_state=seed,
            verbosity=0
        )
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)
        
        acc_scores.append(accuracy_score(y_val, y_pred))
        bal_acc_scores.append(balanced_accuracy_score(y_val, y_pred))
        f1_scores.append(f1_score(y_val, y_pred, average='macro'))
        
        try:
            auc_scores.append(roc_auc_score(y_val, y_proba, multi_class='ovr'))
        except:
            auc_scores.append(np.nan)
    
    return {
        'accuracy_mean': np.mean(acc_scores),
        'accuracy_std': np.std(acc_scores),
        'balanced_accuracy_mean': np.mean(bal_acc_scores),
        'balanced_accuracy_std': np.std(bal_acc_scores),
        'f1_macro_mean': np.mean(f1_scores),
        'f1_macro_std': np.std(f1_scores),
        'roc_auc_ovr_mean': np.nanmean(auc_scores),
        'roc_auc_ovr_std': np.nanstd(auc_scores)
    }


def main():
    print("=" * 80)
    print("ENTRENAMIENTO XGBoost CON FEATURES DISPONIBLES (6 features)")
    print("=" * 80)
    
    # Load data
    X_raw, y_raw = load_data()
    y = y_raw.iloc[:, 0]
    
    print(f"\nTotal samples: {len(X_raw)}")
    print(f"Target classes: {y.unique().tolist()}")
    print(f"Original features: {X_raw.shape[1]}")
    
    # Encode target
    le_target = LabelEncoder()
    y_encoded = le_target.fit_transform(y)
    
    # Prepare available features
    X_avail = prepare_features_available_only(X_raw)
    print(f"\nAvailable features ({X_avail.shape[1]}): {list(X_avail.columns)}")
    print(f"Feature importance coverage: ~47.2% (vs original 100%)")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_avail, y_encoded, test_size=0.15, stratify=y_encoded, random_state=SEED
    )
    
    print(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")
    
    # Train and evaluate
    print("\n" + "-" * 80)
    print("ENTRENAMIENTO Y EVALUACIÓN")
    print("-" * 80)
    
    results = train_evaluate_model(
        X_train, X_test, y_train, y_test, 
        model_name="XGBoost_Available_6F", seed=SEED
    )
    
    print(f"\n--- XGBoost (6 features) ---")
    print(f"Accuracy:          {results['accuracy']:.4f}")
    print(f"Balanced Accuracy: {results['balanced_accuracy']:.4f}")
    print(f"F1 Macro:          {results['f1_macro']:.4f}")
    print(f"ROC-AUC OvR:       {results['roc_auc_ovr']:.4f}")
    
    # Cross-validation
    print("\n" + "-" * 80)
    print("CROSS-VALIDATION (10x5 Repeated Stratified K-Fold)")
    print("-" * 80)
    
    cv_results = cross_validate_model(X_avail, y_encoded, n_splits=10, n_repeats=5, seed=SEED)
    
    print(f"Accuracy:          {cv_results['accuracy_mean']:.4f} +/- {cv_results['accuracy_std']:.4f}")
    print(f"Balanced Accuracy: {cv_results['balanced_accuracy_mean']:.4f} +/- {cv_results['balanced_accuracy_std']:.4f}")
    print(f"F1 Macro:          {cv_results['f1_macro_mean']:.4f} +/- {cv_results['f1_macro_std']:.4f}")
    print(f"ROC-AUC OvR:       {cv_results['roc_auc_ovr_mean']:.4f} +/- {cv_results['roc_auc_ovr_std']:.4f}")
    
    # Classification report
    print("\n" + "-" * 80)
    print("CLASSIFICATION REPORT")
    print("-" * 80)
    
    y_pred = results['model'].predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le_target.classes_))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix:")
    print(cm)
    
    # Save model and artifacts
    print("\n" + "-" * 80)
    print("GUARDANDO ARTEFACTOS")
    print("-" * 80)
    
    results['model'].save_model(os.path.join(MODELS_DIR, 'xgb_available.bin'))
    joblib.dump(le_target, os.path.join(MODELS_DIR, 'le_target_available.pkl'))
    
    # Save scaler for available features
    scaler = StandardScaler()
    scaler.fit(X_train[['Age', 'Height', 'Weight', 'FAF']])
    joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler_available.pkl'))
    
    print(f"Model saved: {os.path.join(MODELS_DIR, 'xgb_available.bin')}")
    print(f"Target encoder saved: {os.path.join(MODELS_DIR, 'le_target_available.pkl')}")
    print(f"Scaler saved: {os.path.join(MODELS_DIR, 'scaler_available.pkl')}")
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("RESUMEN COMPARATIVO")
    print("=" * 80)
    
    print(f"""
Métrica                    XGBoost Original (23F)    XGBoost Disponible (6F)    Delta
─────────────────────────  ───────────────────────   ────────────────────────   ──────
Accuracy                   ~0.9948                    {results['accuracy']:.4f}                  {results['accuracy'] - 0.9948:+.4f}
Balanced Accuracy          ~0.9947                    {results['balanced_accuracy']:.4f}                  {results['balanced_accuracy'] - 0.9947:+.4f}
F1 Macro                   ~0.9947                    {results['f1_macro']:.4f}                  {results['f1_macro'] - 0.9947:+.4f}
ROC-AUC OvR                ~0.9999                    {results['roc_auc_ovr']:.4f}                  {results['roc_auc_ovr'] - 0.9999:+.4f}

Cobertura de features:     100% (23F)                 47.2% (6F)               -52.8%
Features usadas:           Gender,Age,Height,Weight,   Gender,Age,Height,Weight, 
                           family_history,FAVC,FCVC,   SMOKE,FAF
                           NCP,CAEC,CH2O,SCC,FAF,
                           TUE,CALC,MTRANS,SMOKE,BMI
""")
    
    print("PÉRDIDA DE RENDIMIENTO:")
    print(f"  Accuracy:           {(0.9948 - results['accuracy'])*100:.1f}% puntos")
    print(f"  Balanced Accuracy:  {(0.9947 - results['balanced_accuracy'])*100:.1f}% puntos")
    print(f"  F1 Macro:           {(0.9947 - results['f1_macro'])*100:.1f}% puntos")
    print(f"  ROC-AUC OvR:        {(0.9999 - results['roc_auc_ovr'])*100:.1f}% puntos")


if __name__ == "__main__":
    main()
