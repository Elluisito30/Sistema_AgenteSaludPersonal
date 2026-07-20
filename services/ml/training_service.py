import os
import sys
import json
import pandas as pd
import time
import shutil
from datetime import datetime
from typing import Dict, List, Optional

# Add eda/deep_learning to path to import existing training modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "eda", "deep_learning"))

try:
    from config import (
        RANDOM_SEED, MAX_EPOCHS, BATCH_SIZE, VERBOSE,
        EARLY_STOPPING_PATIENCE, EARLY_STOPPING_MIN_DELTA,
        REDUCE_LR_PATIENCE, REDUCE_LR_FACTOR, REDUCE_LR_MIN_LR,
        BEST_MODEL_METRIC, OUTPUT_DIR, GRID_RESULTS_FILENAME,
        HIDDEN_LAYER_CONFIGS, OPTIMIZERS, ACTIVATIONS, REGULARIZATIONS,
        UCI_DATASET_ID, TARGET_COLUMN, FEATURE_COLUMNS, NUM_FEATURES,
        TEST_SIZE, VAL_SIZE, MODEL_FILENAME
    )
    from train_models import grid_search, save_grid_results
    from dataset_loader import load_and_preprocess_data
    from save_best_model import save_all_artifacts
    from evaluate_models import evaluate_model
except ImportError as e:
    print(f"Warning: Could not import training modules: {e}")
    print("Training service will run in simulation mode")
    # Set default values when TensorFlow is not available
    RANDOM_SEED = 42
    MAX_EPOCHS = 300
    BATCH_SIZE = 32
    VERBOSE = 1
    EARLY_STOPPING_PATIENCE = 20
    EARLY_STOPPING_MIN_DELTA = 0.001
    REDUCE_LR_PATIENCE = 5
    REDUCE_LR_FACTOR = 0.5
    REDUCE_LR_MIN_LR = 1e-6
    BEST_MODEL_METRIC = "val_accuracy"
    OUTPUT_DIR = "eda/deep_learning/output"
    GRID_RESULTS_FILENAME = "grid_results.csv"
    HIDDEN_LAYER_CONFIGS = []
    OPTIMIZERS = ["adam"]
    ACTIVATIONS = ["relu"]
    REGULARIZATIONS = ["dropout"]
    UCI_DATASET_ID = 544
    TARGET_COLUMN = "NObeyesdad"
    FEATURE_COLUMNS = []
    NUM_FEATURES = 11
    TEST_SIZE = 0.15
    VAL_SIZE = 0.15
    MODEL_FILENAME = "best_model.h5"
    grid_search = None
    save_grid_results = None
    load_and_preprocess_data = None
    save_all_artifacts = None
    evaluate_model = None

class TrainingService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.eda_dir = os.path.join(self.base_dir, "eda")
        self.models_dir = os.path.join(self.eda_dir, "models")
        self.output_dir = os.path.join(self.eda_dir, "deep_learning", "output")
        self.grid_results_path = os.path.join(self.output_dir, GRID_RESULTS_FILENAME)
        
    def get_dataset_info(self) -> Dict:
        """Get information about the dataset used for training."""
        return {
            "source": "UCI Machine Learning Repository",
            "dataset_id": UCI_DATASET_ID if 'UCI_DATASET_ID' in globals() else 544,
            "target_column": TARGET_COLUMN if 'TARGET_COLUMN' in globals() else "NObeyesdad",
            "num_features": NUM_FEATURES if 'NUM_FEATURES' in globals() else 11,
            "feature_columns": FEATURE_COLUMNS if 'FEATURE_COLUMNS' in globals() else [
                "Age", "Gender", "Height", "Weight", "SMOKE", "FAF", "BMI",
                "family_history", "FAVC", "FCVC", "CH2O"
            ],
            "test_size": TEST_SIZE if 'TEST_SIZE' in globals() else 0.15,
            "val_size": VAL_SIZE if 'VAL_SIZE' in globals() else 0.15
        }
    
    def get_hyperparameters(self) -> Dict:
        """Get current hyperparameter configuration."""
        return {
            "max_epochs": MAX_EPOCHS if 'MAX_EPOCHS' in globals() else 300,
            "batch_size": BATCH_SIZE if 'BATCH_SIZE' in globals() else 32,
            "random_seed": RANDOM_SEED if 'RANDOM_SEED' in globals() else 42,
            "early_stopping_patience": EARLY_STOPPING_PATIENCE if 'EARLY_STOPPING_PATIENCE' in globals() else 20,
            "early_stopping_min_delta": EARLY_STOPPING_MIN_DELTA if 'EARLY_STOPPING_MIN_DELTA' in globals() else 1e-4,
            "reduce_lr_patience": REDUCE_LR_PATIENCE if 'REDUCE_LR_PATIENCE' in globals() else 10,
            "reduce_lr_factor": REDUCE_LR_FACTOR if 'REDUCE_LR_FACTOR' in globals() else 0.5,
            "reduce_lr_min_lr": REDUCE_LR_MIN_LR if 'REDUCE_LR_MIN_LR' in globals() else 1e-6,
            "grid_search_space": {
                "hidden_layer_configs": [
                    {"name": cfg.get("name", "unknown"), "units": cfg.get("units", [])}
                    for cfg in (HIDDEN_LAYER_CONFIGS if 'HIDDEN_LAYER_CONFIGS' in globals() else [])
                ],
                "optimizers": OPTIMIZERS if 'OPTIMIZERS' in globals() else ["adam", "rmsprop"],
                "activations": ACTIVATIONS if 'ACTIVATIONS' in globals() else ["relu", "leaky_relu"],
                "regularizations": REGULARIZATIONS if 'REGULARIZATIONS' in globals() else ["dropout", "batch_norm"]
            }
        }
    
    def get_training_history(self) -> Dict:
        """Get training history from both MLP and classical training results."""
        all_results = []
        last_updated = None
        
        # Read MLP training history
        if os.path.exists(self.grid_results_path):
            try:
                df = pd.read_csv(self.grid_results_path)
                mlp_results = df.to_dict(orient="records")
                all_results.extend(mlp_results)
                mlp_mtime = os.path.getmtime(self.grid_results_path)
                if last_updated is None or mlp_mtime > last_updated:
                    last_updated = mlp_mtime
            except Exception as e:
                print(f"Error reading MLP training history: {e}")
        
        # Read classical training history
        classical_results_path = os.path.join(self.eda_dir, "classical_output", "classical_training_results.csv")
        if os.path.exists(classical_results_path):
            try:
                df = pd.read_csv(classical_results_path)
                classical_results = df.to_dict(orient="records")
                
                # Parse cv_results from JSON strings
                for result in classical_results:
                    if 'cv_results' in result and pd.notna(result['cv_results']):
                        try:
                            import json
                            result['cv_results'] = json.loads(result['cv_results'])
                        except:
                            result['cv_results'] = None
                    else:
                        result['cv_results'] = None
                
                all_results.extend(classical_results)
                classical_mtime = os.path.getmtime(classical_results_path)
                if last_updated is None or classical_mtime > last_updated:
                    last_updated = classical_mtime
            except Exception as e:
                print(f"Error reading classical training history: {e}")
        
        if all_results:
            return {
                "has_history": True,
                "total_runs": len(all_results),
                "last_updated": datetime.fromtimestamp(last_updated).isoformat() if last_updated else None,
                "results": all_results
            }
        
        return {
            "has_history": False,
            "total_runs": 0,
            "last_updated": None,
            "results": []
        }
    
    def run_training(self) -> Dict:
        """Execute the training pipeline."""
        try:
            # Check if training modules are available
            if 'grid_search' not in globals():
                return {
                    "success": False,
                    "error": "Training modules not available. Please ensure eda/deep_learning is properly configured."
                }
            
            start_time = time.time()
            
            # Load data
            print("Loading dataset...")
            X_train, X_val, X_test, y_train, y_val, y_test, scaler, label_encoder = load_and_preprocess_data()
            num_features = X_train.shape[1]
            num_classes = len(label_encoder.classes_)
            
            # Run grid search
            print("Starting grid search...")
            results, best = grid_search(num_features, num_classes, X_train, y_train, X_val, y_val)
            
            # Save results
            save_grid_results(results)
            
            # Evaluate best model on test set
            print("Evaluating best model on test set...")
            test_metrics = evaluate_model(best["model"], X_test, y_test, label_encoder)
            
            # Save all artifacts including best model
            print("Saving artifacts...")
            save_all_artifacts(
                best["model"],
                best["history"],
                scaler,
                label_encoder,
                test_metrics,
                best["config"],
                OUTPUT_DIR
            )
            
            # Copy best model to main models directory for validation
            trained_model_path = os.path.join(self.output_dir, MODEL_FILENAME)
            target_model_path = os.path.join(self.models_dir, "obesity_mlp.h5")
            
            if os.path.exists(trained_model_path):
                shutil.copy2(trained_model_path, target_model_path)
                print(f"Copied trained model to: {target_model_path}")
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "message": "Training completed successfully",
                "elapsed_time_seconds": elapsed_time,
                "total_models_trained": len(results),
                "best_model": {
                    "name": best["config"]["name"],
                    "val_accuracy": best["val_accuracy"],
                    "best_epoch": best["best_epoch"],
                    "train_time": best["train_time"],
                    "config": best["config"],
                    "test_metrics": test_metrics
                },
                "all_results": [
                    {
                        "name": r["config"]["name"],
                        "val_accuracy": r["val_accuracy"],
                        "best_epoch": r["best_epoch"],
                        "train_time": r["train_time"],
                        "config": r["config"]
                    }
                    for r in results
                ]
            }
        except Exception as e:
            print(f"Error during training: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def run_classical_training(self) -> Dict:
        """Execute classical ML training (XGBoost, RandomForest)."""
        try:
            # Import classical training module
            classical_script_path = os.path.join(self.eda_dir, "classical_training.py")
            
            print(f"Checking for classical training script at: {classical_script_path}")
            
            if not os.path.exists(classical_script_path):
                return {
                    "success": False,
                    "error": "Classical training script not found at: " + classical_script_path
                }
            
            # Add eda directory to path
            sys.path.insert(0, self.eda_dir)
            
            # Import and run
            print("Importing classical_training module...")
            import classical_training
            print("Running classical training...")
            start_time = time.time()
            results = classical_training.run_classical_training()
            elapsed_time = time.time() - start_time
            
            print(f"Classical training completed in {elapsed_time:.2f}s")
            
            return {
                "success": True,
                "message": "Classical training completed successfully",
                "elapsed_time_seconds": elapsed_time,
                "results": results
            }
        except Exception as e:
            print(f"Error during classical training: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def run_all_training(self) -> Dict:
        """Execute all training (MLP + Classical XGBoost/RF)."""
        try:
            start_time = time.time()
            all_results = {
                "mlp": None,
                "classical": None
            }
            
            # Step 1: Train Classical models first (always available)
            try:
                print("Starting Classical training...")
                classical_result = self.run_classical_training()
                all_results["classical"] = classical_result
                if not classical_result.get("success"):
                    print(f"Classical training failed: {classical_result.get('error')}")
            except Exception as e:
                print(f"Classical training error: {e}")
                all_results["classical"] = {"success": False, "error": str(e)}
            
            # Step 2: Train MLP (if available)
            try:
                print("Starting MLP training...")
                mlp_result = self.run_training()
                all_results["mlp"] = mlp_result
                if not mlp_result.get("success"):
                    print(f"MLP training failed: {mlp_result.get('error')}")
            except Exception as e:
                print(f"MLP training error: {e}")
                all_results["mlp"] = {"success": False, "error": str(e)}
            
            elapsed_time = time.time() - start_time
            
            # Check if at least one succeeded
            mlp_success = all_results["mlp"].get("success", False) if all_results["mlp"] else False
            classical_success = all_results["classical"].get("success", False) if all_results["classical"] else False
            
            return {
                "success": mlp_success or classical_success,
                "message": "All training completed",
                "elapsed_time_seconds": elapsed_time,
                "results": all_results
            }
        except Exception as e:
            print(f"Error during all training: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_status(self) -> Dict:
        """Get status of trained models."""
        model_files = []
        if os.path.exists(self.models_dir):
            for file in os.listdir(self.models_dir):
                file_path = os.path.join(self.models_dir, file)
                if os.path.isfile(file_path):
                    model_files.append({
                        "name": file,
                        "size_bytes": os.path.getsize(file_path),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
        
        return {
            "models_dir": self.models_dir,
            "model_count": len(model_files),
            "models": model_files
        }

    def get_model_type(self) -> Dict:
        """Check if using pretrained or custom models."""
        training_output_dir = os.path.join(self.eda_dir, "deep_learning", "output")
        classical_output_dir = os.path.join(self.eda_dir, "classical_output")
        
        # Check for custom MLP
        custom_mlp = os.path.exists(os.path.join(training_output_dir, "best_model.h5"))
        
        # Check for custom classical models
        custom_xgb = os.path.exists(os.path.join(classical_output_dir, "classical_training_results.csv"))
        
        # Check if models were recently trained (within last 24 hours)
        has_custom = custom_mlp or custom_xgb
        
        return {
            "model_type": "custom" if has_custom else "pretrained",
            "has_custom_mlp": custom_mlp,
            "has_custom_classical": custom_xgb,
            "message": "Usando modelos personalizados" if has_custom else "Usando modelos pre-entrenados"
        }

training_service = TrainingService()
