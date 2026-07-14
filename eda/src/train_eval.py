
"""
Training and evaluation script: NO DATA LEAKAGE, Repeated Stratified K-Fold, statistical tests
"""
import warnings
warnings.filterwarnings('ignore')

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Get script's directory to use absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Models directory is eda/models (parent of src)
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

from sklearn.model_selection import (
    train_test_split, RepeatedStratifiedKFold
)
from sklearn.metrics import (
    accuracy_score, f1_score, balanced_accuracy_score, 
    cohen_kappa_score, roc_auc_score, confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import friedmanchisquare
import scikit_posthocs as sp

import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

import joblib
from preprocessing import (
    load_data, fit_preprocessing, transform_preprocessing,
    fit_target, transform_target
)


def set_random_seeds(seed=42):
    """
    Set all random seeds for 100% reproducibility.
    """
    np.random.seed(seed)
    tf.random.set_seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)


def build_mlp(input_shape, num_classes):
    """
    Build MLP model as per methodology.
    """
    model = Sequential([
        Dense(64, activation='relu', input_shape=(input_shape,)),
        Dropout(0.15),
        Dense(32, activation='relu'),
        Dropout(0.15),
        Dense(16, activation='relu'),
        Dropout(0.15),
        Dense(num_classes, activation='softmax')
    ])
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    return model


def evaluate_model(y_true, y_pred, y_pred_proba=None):
    """
    Compute all metrics.
    """
    metrics = {}
    metrics['accuracy'] = accuracy_score(y_true, y_pred)
    metrics['balanced_accuracy'] = balanced_accuracy_score(y_true, y_pred)
    metrics['cohen_kappa'] = cohen_kappa_score(y_true, y_pred)
    metrics['f1_macro'] = f1_score(y_true, y_pred, average='macro')
    metrics['f1_weighted'] = f1_score(y_true, y_pred, average='weighted')

    if y_pred_proba is not None:
        try:
            metrics['roc_auc_ovr'] = roc_auc_score(y_true, y_pred_proba, multi_class='ovr')
        except Exception:
            metrics['roc_auc_ovr'] = np.nan
    else:
        metrics['roc_auc_ovr'] = np.nan

    return metrics


def run_repeated_kfold_experiment(X, y, n_splits=10, n_repeats=5, seed=42):
    """
    Run Repeated Stratified K-Fold with NO DATA LEAKAGE.
    """
    print(f"\n=== Running {n_repeats}x{n_splits} Repeated Stratified K-Fold ===")
    set_random_seeds(seed)

    # 1. Split into Hold-out Test (15%) and Train-Val (85%) FIRST, before any preprocessing!
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=seed
    )

    model_names = ['Logistic Regression', 'Random Forest', 'XGBoost', 'MLP']
    results_list = []
    fold_scores = {model: [] for model in model_names}

    # 2. Define cross-validation strategy
    rkf = RepeatedStratifiedKFold(
        n_splits=n_splits, n_repeats=n_repeats, random_state=seed
    )
    fold_counter = 0

    # 3. Cross-validation loop
    for train_idx, val_idx in rkf.split(X_train_val, y_train_val):
        fold_counter +=1
        print(f"  Fold/Repeat: {fold_counter}/{n_splits*n_repeats}")

        # Get this fold's train and validation (as DataFrames, not numpy!)
        X_tr_fold = X_train_val.iloc[train_idx]
        X_val_fold = X_train_val.iloc[val_idx]
        y_tr_fold = y_train_val.iloc[train_idx]
        y_val_fold = y_train_val.iloc[val_idx]

        # Fit preprocessing ONLY ON THIS FOLD'S TRAIN DATA!
        binary_encoders, col_transformer = fit_preprocessing(X_tr_fold)
        target_encoder = fit_target(y_tr_fold)

        # Transform both train and val
        X_tr_processed = transform_preprocessing(X_tr_fold, binary_encoders, col_transformer)
        X_val_processed = transform_preprocessing(X_val_fold, binary_encoders, col_transformer)
        y_tr_enc = transform_target(y_tr_fold, target_encoder)
        y_val_enc = transform_target(y_val_fold, target_encoder)
        num_classes = len(target_encoder.classes_)

        # --- Train and Evaluate each model ---
        # 1. Logistic Regression
        logreg = LogisticRegression(max_iter=500, random_state=seed)
        logreg.fit(X_tr_processed, y_tr_enc)
        y_pred_logreg = logreg.predict(X_val_processed)
        y_pred_proba_logreg = logreg.predict_proba(X_val_processed)
        metrics_logreg = evaluate_model(y_val_enc, y_pred_logreg, y_pred_proba_logreg)
        results_list.append({
            'model': 'Logistic Regression', 'fold': fold_counter, **metrics_logreg
        })
        fold_scores['Logistic Regression'].append(metrics_logreg['f1_macro'])

        # 2. Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=seed)
        rf.fit(X_tr_processed, y_tr_enc)
        y_pred_rf = rf.predict(X_val_processed)
        y_pred_proba_rf = rf.predict_proba(X_val_processed)
        metrics_rf = evaluate_model(y_val_enc, y_pred_rf, y_pred_proba_rf)
        results_list.append({
            'model': 'Random Forest', 'fold': fold_counter, **metrics_rf
        })
        fold_scores['Random Forest'].append(metrics_rf['f1_macro'])

        #3. XGBoost
        xgb_model = xgb.XGBClassifier(
            n_estimators=100, objective='multi:softprob', num_class=num_classes,
            random_state=seed, verbosity=0
        )
        xgb_model.fit(X_tr_processed, y_tr_enc)
        y_pred_xgb = xgb_model.predict(X_val_processed)
        y_pred_proba_xgb = xgb_model.predict_proba(X_val_processed)
        metrics_xgb = evaluate_model(y_val_enc, y_pred_xgb, y_pred_proba_xgb)
        results_list.append({
            'model': 'XGBoost', 'fold': fold_counter, **metrics_xgb
        })
        fold_scores['XGBoost'].append(metrics_xgb['f1_macro'])

        #4. MLP
        mlp = build_mlp(input_shape=X_tr_processed.shape[1], num_classes=num_classes)
        early_stopping = EarlyStopping(
            monitor='val_loss', patience=20, restore_best_weights=True, verbose=0
        )
        mlp.fit(
            X_tr_processed, y_tr_enc,
            validation_data=(X_val_processed, y_val_enc),
            epochs=300, batch_size=32,
            callbacks=[early_stopping],
            verbose=0
        )
        y_pred_proba_mlp = mlp.predict(X_val_processed, verbose=0)
        y_pred_mlp = y_pred_proba_mlp.argmax(axis=-1)
        metrics_mlp = evaluate_model(y_val_enc, y_pred_mlp, y_pred_proba_mlp)
        results_list.append({
            'model': 'MLP', 'fold': fold_counter, **metrics_mlp
        })
        fold_scores['MLP'].append(metrics_mlp['f1_macro'])

    # --- Final Hold-out Test Evaluation ---
    print("\n=== Final Hold-out Test Set Evaluation ===")
    final_test_results = []

    # Fit preprocessing ON FULL TRAIN-VAL ONLY!
    binary_encoders_final, col_transformer_final = fit_preprocessing(X_train_val)
    target_encoder_final = fit_target(y_train_val)
    X_train_val_processed = transform_preprocessing(X_train_val, binary_encoders_final, col_transformer_final)
    X_test_processed = transform_preprocessing(X_test, binary_encoders_final, col_transformer_final)
    y_train_val_enc = transform_target(y_train_val, target_encoder_final)
    y_test_enc = transform_target(y_test, target_encoder_final)
    num_classes = len(target_encoder_final.classes_)

    # Train final models
    #1. Logistic Regression
    logreg_final = LogisticRegression(max_iter=500, random_state=seed)
    logreg_final.fit(X_train_val_processed, y_train_val_enc)
    y_pred_logreg_test = logreg_final.predict(X_test_processed)
    y_pred_proba_logreg_test = logreg_final.predict_proba(X_test_processed)
    final_test_results.append({
        'model': 'Logistic Regression',
        **evaluate_model(y_test_enc, y_pred_logreg_test, y_pred_proba_logreg_test)
    })

    #2. Random Forest
    rf_final = RandomForestClassifier(n_estimators=100, random_state=seed)
    rf_final.fit(X_train_val_processed, y_train_val_enc)
    y_pred_rf_test = rf_final.predict(X_test_processed)
    y_pred_proba_rf_test = rf_final.predict_proba(X_test_processed)
    final_test_results.append({
        'model': 'Random Forest',
        **evaluate_model(y_test_enc, y_pred_rf_test, y_pred_proba_rf_test)
    })

    #3. XGBoost
    xgb_final = xgb.XGBClassifier(
        n_estimators=100, objective='multi:softprob', num_class=num_classes,
        random_state=seed, verbosity=0
    )
    xgb_final.fit(X_train_val_processed, y_train_val_enc)
    y_pred_xgb_test = xgb_final.predict(X_test_processed)
    y_pred_proba_xgb_test = xgb_final.predict_proba(X_test_processed)
    final_test_results.append({
        'model': 'XGBoost',
        **evaluate_model(y_test_enc, y_pred_xgb_test, y_pred_proba_xgb_test)
    })

    #4. MLP
    mlp_final = build_mlp(input_shape=X_train_val_processed.shape[1], num_classes=num_classes)
    early_stopping_final = EarlyStopping(
        monitor='val_loss', patience=20, restore_best_weights=True, verbose=1
    )
    # Split Train-Val into small train/val for final MLP training early stopping
    X_tr_final, X_val_final, y_tr_final, y_val_final = train_test_split(
        X_train_val_processed, y_train_val_enc, test_size=0.1765,
        stratify=y_train_val_enc, random_state=seed
    )
    history_final = mlp_final.fit(
        X_tr_final, y_tr_final,
        validation_data=(X_val_final, y_val_final),
        epochs=300, batch_size=32,
        callbacks=[early_stopping_final],
        verbose=1
    )
    y_pred_proba_mlp_test = mlp_final.predict(X_test_processed, verbose=0)
    y_pred_mlp_test = y_pred_proba_mlp_test.argmax(axis=-1)
    final_test_results.append({
        'model': 'MLP',
        **evaluate_model(y_test_enc, y_pred_mlp_test, y_pred_proba_mlp_test)
    })

    # --- Statistical Tests ---
    print("\n=== Statistical Tests ===")
    scores_array = np.array([
        fold_scores['Logistic Regression'],
        fold_scores['Random Forest'],
        fold_scores['XGBoost'],
        fold_scores['MLP']
    ])
    stat, p_value = friedmanchisquare(*scores_array)
    print(f"Friedman Test: statistic = {stat:.4f}, p-value = {p_value:.4f}")

    nemenyi_results = None
    if p_value < 0.05:
        print("\nFriedman test significant (p <0.05). Performing Nemenyi Post-Hoc Test...")
        nemenyi_results = sp.posthoc_nemenyi_friedman(scores_array.T)
        nemenyi_results.columns = model_names
        nemenyi_results.index = model_names
    else:
        print("\nFriedman test not significant (p≥0.05). No post-hoc test needed.")

    # --- Save everything ---
    results_df = pd.DataFrame(results_list)
    final_test_df = pd.DataFrame(final_test_results)
    stats_df = pd.DataFrame([{'test': 'Friedman', 'statistic': stat, 'p_value': p_value}])

    # Save dataframes
    results_df.to_csv(os.path.join(MODELS_DIR, 'cv_results.csv'), index=False)
    final_test_df.to_csv(os.path.join(MODELS_DIR, 'holdout_test_results.csv'), index=False)
    stats_df.to_csv(os.path.join(MODELS_DIR, 'statistical_results.csv'), index=False)
    if nemenyi_results is not None:
        nemenyi_results.to_csv(os.path.join(MODELS_DIR, 'nemenyi_results.csv'))

    # Save models and preprocessors
    joblib.dump(logreg_final, os.path.join(MODELS_DIR, 'logreg.pkl'))
    joblib.dump(rf_final, os.path.join(MODELS_DIR, 'rf.pkl'))
    xgb_final.save_model(os.path.join(MODELS_DIR, 'xgb.json'))
    mlp_final.save(os.path.join(MODELS_DIR, 'obesity_mlp.h5'))
    joblib.dump(col_transformer_final, os.path.join(MODELS_DIR, 'preprocessor.pkl'))
    joblib.dump(binary_encoders_final, os.path.join(MODELS_DIR, 'binary_encoders.pkl'))
    joblib.dump(target_encoder_final, os.path.join(MODELS_DIR, 'le_target.pkl'))

    # Save plots
    cm = confusion_matrix(y_test_enc, y_pred_mlp_test)
    plt.figure(figsize=(10,8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=target_encoder_final.classes_,
                yticklabels=target_encoder_final.classes_)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix: MLP (Hold-Out Test)')
    plt.tight_layout()
    plt.savefig(os.path.join(MODELS_DIR, 'confusion_matrix_mlp_test.png'))
    plt.close()

    plt.figure(figsize=(12,4))
    plt.subplot(121)
    plt.plot(history_final.history['loss'], label='Train Loss')
    plt.plot(history_final.history['val_loss'], label='Val Loss')
    plt.title('Training and Validation Loss (Final MLP)')
    plt.legend()
    plt.subplot(122)
    plt.plot(history_final.history['accuracy'], label='Train Accuracy')
    plt.plot(history_final.history['val_accuracy'], label='Val Accuracy')
    plt.title('Training and Validation Accuracy (Final MLP)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(MODELS_DIR, 'mlp_final_training_history.png'))
    plt.close()

    print("\n=== Experiment Complete ===")
    print("\n--- Final Hold-Out Test Results ---")
    print(final_test_df.round(4).to_string(index=False))

    return results_df, final_test_df, stats_df, nemenyi_results


def main():
    """
    Main entry point of the experiment.
    """
    print("="*80)
    print("OBESITY LEVEL PREDICTION EXPERIMENT (NO DATA LEAKAGE)")
    print("="*80)

    set_random_seeds(42)

    # Load data ONLY, NO PREPROCESSING YET!
    df = load_data()
    X = df.drop('NObeyesdad', axis=1)
    y = df['NObeyesdad']

    print(f"\nTotal records: {len(df)}")
    print(f"Classes: {y.unique().tolist()}")

    # Run experiment
    run_repeated_kfold_experiment(X, y, n_splits=10, n_repeats=5, seed=42)


if __name__ == "__main__":
    main()
