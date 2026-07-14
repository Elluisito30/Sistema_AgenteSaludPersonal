"""
Central configuration for Deep Learning experimentation pipeline.

Defines all hyperparameters, grid search space, paths, and constants.
Every other module imports from here — no hardcoded values elsewhere.
"""

import os

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# =============================================================================
# REPRODUCIBILITY
# =============================================================================
RANDOM_SEED = 42

# =============================================================================
# DATASET — UCI Obesity Dataset (id=544)
# =============================================================================
UCI_DATASET_ID = 544
TARGET_COLUMN = "NObeyesdad"

FEATURE_COLUMNS = [
    "Age",
    "Gender",
    "Height",
    "Weight",
    "SMOKE",
    "FAF",
    "BMI",
    "family_history",
    "FAVC",
    "FCVC",
    "CH2O",
]

NUM_FEATURES = len(FEATURE_COLUMNS)  # 11

# =============================================================================
# DATA SPLIT
# =============================================================================
TEST_SIZE = 0.15
VAL_SIZE = 0.15  # of remaining 85%

# =============================================================================
# GRID SEARCH SPACE
# =============================================================================
# Each combination produces one unique architecture.
# 3 layer_configs x 2 optimizers x 2 activations x 2 regularizers = 24 models

HIDDEN_LAYER_CONFIGS = [
    {"name": "1layer", "units": [128]},
    {"name": "2layers", "units": [256, 128]},
    {"name": "3layers", "units": [512, 256, 128]},
]

OPTIMIZERS = ["adam", "rmsprop"]

ACTIVATIONS = ["relu", "leaky_relu"]

REGULARIZATIONS = ["dropout", "batch_norm"]

# =============================================================================
# MLP DEFAULTS
# =============================================================================
DROPOUT_RATE = 0.3
OUTPUT_ACTIVATION = "softmax"
LOSS_FUNCTION = "sparse_categorical_crossentropy"

# =============================================================================
# TRAINING DEFAULTS
# =============================================================================
MAX_EPOCHS = 300
BATCH_SIZE = 32
VERBOSE = 1

# =============================================================================
# CALLBACKS
# =============================================================================
EARLY_STOPPING_PATIENCE = 20
EARLY_STOPPING_MIN_DELTA = 1e-4
REDUCE_LR_PATIENCE = 10
REDUCE_LR_FACTOR = 0.5
REDUCE_LR_MIN_LR = 1e-6

# =============================================================================
# SELECTION CRITERION
# =============================================================================
BEST_MODEL_METRIC = "val_accuracy"

# =============================================================================
# MODEL SAVE FORMAT
# =============================================================================
MODEL_FILENAME = "best_model.h5"
HISTORY_FILENAME = "history.pkl"
SCALER_FILENAME = "scaler.pkl"
LABEL_ENCODER_FILENAME = "label_encoder.pkl"
METRICS_FILENAME = "metrics.json"
GRID_RESULTS_FILENAME = "grid_results.csv"
