"""
Classical ML Training Script for XGBoost and RandomForest

Trains XGBoost and RandomForest models with grid search on UCI Obesity Dataset.
Saves trained models to eda/models/ directory.
"""

import os
import sys
import time
import joblib
import numpy as np
import pandas as pd
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "classical_output")

# Dataset config
UCI_DATASET_ID = 544
TARGET_COLUMN = "NObeyesdad"
FEATURE_COLUMNS = [
    "Age", "Gender", "Height", "Weight", "SMOKE", "FAF", "BMI",
    "family_history_with_overweight", "FAVC", "FCVC", "CH2O"
]

# Training config
RANDOM_SEED = 42
TEST_SIZE = 0.15
VAL_SIZE = 0.15

def load_and_preprocess_data():
    """Load and preprocess UCI Obesity Dataset."""
    print("Loading UCI Obesity Dataset...")
    obesity_dataset = fetch_ucirepo(id=UCI_DATASET_ID)
    X = obesity_dataset.data.features
    y = obesity_dataset.data.targets
    
    # Select only the 11 features used in the system
    X = X[FEATURE_COLUMNS]
    
    # Encode target
    le_target = LabelEncoder()
    y_encoded = le_target.fit_transform(y)
    
    # Encode categorical features
    label_encoders = {}
    for col in X.columns:
        if X[col].dtype == 'object':
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            label_encoders[col] = le
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y_encoded
    )
    
    # Further split train into train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=VAL_SIZE/(1-TEST_SIZE), random_state=RANDOM_SEED, stratify=y_train
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"Train: {X_train_scaled.shape}, Val: {X_val_scaled.shape}, Test: {X_test_scaled.shape}")
    print(f"Classes: {le_target.classes_}")
    
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, scaler, le_target

def train_xgboost(X_train, y_train, X_val, y_val):
    """Train XGBoost with grid search."""
    print("\n" + "="*50)
    print("Training XGBoost")
    print("="*50)
    
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'subsample': [0.8, 1.0]
    }
    
    xgb_model = xgb.XGBClassifier(
        random_state=RANDOM_SEED,
        eval_metric='mlogloss',
        use_label_encoder=False
    )
    
    grid_search = GridSearchCV(
        xgb_model, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=1, return_train_score=True
    )
    
    start_time = time.time()
    grid_search.fit(X_train, y_train)
    elapsed_time = time.time() - start_time
    
    best_model = grid_search.best_estimator_
    val_accuracy = best_model.score(X_val, y_val)
    
    # Extract cross-validation results
    cv_results = {
        'mean_test_score': grid_search.cv_results_['mean_test_score'].tolist(),
        'std_test_score': grid_search.cv_results_['std_test_score'].tolist(),
        'params': grid_search.cv_results_['params'],
        'mean_train_score': grid_search.cv_results_['mean_train_score'].tolist()
    }
    
    print(f"Best params: {grid_search.best_params_}")
    print(f"Val accuracy: {val_accuracy:.4f}")
    print(f"Training time: {elapsed_time:.2f}s")
    
    return best_model, {
        "best_params": grid_search.best_params_,
        "val_accuracy": val_accuracy,
        "training_time": elapsed_time,
        "cv_results": cv_results
    }

def train_randomforest(X_train, y_train, X_val, y_val):
    """Train RandomForest with grid search."""
    print("\n" + "="*50)
    print("Training RandomForest")
    print("="*50)
    
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [5, 10, 15],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    
    rf_model = RandomForestClassifier(random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        rf_model, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=1, return_train_score=True
    )
    
    start_time = time.time()
    grid_search.fit(X_train, y_train)
    elapsed_time = time.time() - start_time
    
    best_model = grid_search.best_estimator_
    val_accuracy = best_model.score(X_val, y_val)
    
    # Extract cross-validation results
    cv_results = {
        'mean_test_score': grid_search.cv_results_['mean_test_score'].tolist(),
        'std_test_score': grid_search.cv_results_['std_test_score'].tolist(),
        'params': grid_search.cv_results_['params'],
        'mean_train_score': grid_search.cv_results_['mean_train_score'].tolist()
    }
    
    print(f"Best params: {grid_search.best_params_}")
    print(f"Val accuracy: {val_accuracy:.4f}")
    print(f"Training time: {elapsed_time:.2f}s")
    
    return best_model, {
        "best_params": grid_search.best_params_,
        "val_accuracy": val_accuracy,
        "training_time": elapsed_time,
        "cv_results": cv_results
    }

def train_logistic_regression(X_train, y_train, X_val, y_val):
    """Train Logistic Regression with grid search."""
    print("\n" + "="*50)
    print("Training Logistic Regression")
    print("="*50)
    
    param_grid = {
        'C': [0.1, 1, 10],
        'solver': ['liblinear', 'lbfgs'],
        'max_iter': [100, 200]
    }
    
    lr_model = LogisticRegression(random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        lr_model, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=1, return_train_score=True
    )
    
    start_time = time.time()
    grid_search.fit(X_train, y_train)
    elapsed_time = time.time() - start_time
    
    best_model = grid_search.best_estimator_
    val_accuracy = best_model.score(X_val, y_val)
    
    # Extract cross-validation results
    cv_results = {
        'mean_test_score': grid_search.cv_results_['mean_test_score'].tolist(),
        'std_test_score': grid_search.cv_results_['std_test_score'].tolist(),
        'params': grid_search.cv_results_['params'],
        'mean_train_score': grid_search.cv_results_['mean_train_score'].tolist()
    }
    
    print(f"Best params: {grid_search.best_params_}")
    print(f"Val accuracy: {val_accuracy:.4f}")
    print(f"Training time: {elapsed_time:.2f}s")
    
    return best_model, {
        "best_params": grid_search.best_params_,
        "val_accuracy": val_accuracy,
        "training_time": elapsed_time,
        "cv_results": cv_results
    }

def save_model(model, model_name, models_dir=MODELS_DIR):
    """Save trained model to disk."""
    os.makedirs(models_dir, exist_ok=True)
    
    if model_name == "xgboost":
        model_path = os.path.join(models_dir, "xgb_11f.bin")
        model.save_model(model_path)
    elif model_name == "randomforest":
        model_path = os.path.join(models_dir, "rf.pkl")
        joblib.dump(model, model_path)
    elif model_name == "logistic_regression":
        model_path = os.path.join(models_dir, "logreg.pkl")
        joblib.dump(model, model_path)
    else:
        model_path = os.path.join(models_dir, f"{model_name}.pkl")
        joblib.dump(model, model_path)
    
    print(f"Model saved to: {model_path}")
    return model_path

def save_training_results(results, output_dir=OUTPUT_DIR):
    """Save training results to CSV."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert cv_results dict to JSON string for CSV storage
    for result in results:
        if 'cv_results' in result and result['cv_results']:
            import json
            result['cv_results'] = json.dumps(result['cv_results'])
    
    df = pd.DataFrame(results)
    results_path = os.path.join(output_dir, "classical_training_results.csv")
    df.to_csv(results_path, index=False)
    
    print(f"Results saved to: {results_path}")
    return results_path

def run_classical_training():
    """Run complete classical ML training pipeline."""
    print("="*50)
    print("CLASSICAL ML TRAINING PIPELINE")
    print("="*50)
    
    # Load data
    X_train, X_val, X_test, y_train, y_val, y_test, scaler, le_target = load_and_preprocess_data()
    
    # Train models
    results = []
    
    # XGBoost
    xgb_model, xgb_metrics = train_xgboost(X_train, y_train, X_val, y_val)
    xgb_path = save_model(xgb_model, "xgboost")
    
    xgb_test_acc = xgb_model.score(X_test, y_test)
    results.append({
        "model": "XGBoost",
        "val_accuracy": xgb_metrics["val_accuracy"],
        "test_accuracy": xgb_test_acc,
        "training_time": xgb_metrics["training_time"],
        "best_params": str(xgb_metrics["best_params"]),
        "model_path": xgb_path,
        "cv_results": xgb_metrics.get("cv_results", {})
    })
    
    # RandomForest
    rf_model, rf_metrics = train_randomforest(X_train, y_train, X_val, y_val)
    rf_path = save_model(rf_model, "randomforest")
    
    rf_test_acc = rf_model.score(X_test, y_test)
    results.append({
        "model": "RandomForest",
        "val_accuracy": rf_metrics["val_accuracy"],
        "test_accuracy": rf_test_acc,
        "training_time": rf_metrics["training_time"],
        "best_params": str(rf_metrics["best_params"]),
        "model_path": rf_path,
        "cv_results": rf_metrics.get("cv_results", {})
    })
    
    # Logistic Regression
    lr_model, lr_metrics = train_logistic_regression(X_train, y_train, X_val, y_val)
    lr_path = save_model(lr_model, "logistic_regression")
    
    lr_test_acc = lr_model.score(X_test, y_test)
    results.append({
        "model": "LogisticRegression",
        "val_accuracy": lr_metrics["val_accuracy"],
        "test_accuracy": lr_test_acc,
        "training_time": lr_metrics["training_time"],
        "best_params": str(lr_metrics["best_params"]),
        "model_path": lr_path,
        "cv_results": lr_metrics.get("cv_results", {})
    })
    
    # Save results
    save_training_results(results)
    
    # Print summary
    print("\n" + "="*50)
    print("TRAINING SUMMARY")
    print("="*50)
    for result in results:
        print(f"\n{result['model']}:")
        print(f"  Val Accuracy: {result['val_accuracy']:.4f}")
        print(f"  Test Accuracy: {result['test_accuracy']:.4f}")
        print(f"  Training Time: {result['training_time']:.2f}s")
    
    return results

if __name__ == "__main__":
    run_classical_training()
