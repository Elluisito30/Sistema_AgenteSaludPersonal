# Deep Learning — Obesity Classification with MLPs

## Overview

This module implements a **standalone, reproducible** deep learning research pipeline
for obesity classification using Multi-Layer Perceptrons (MLPs).

It uses the **same 11 features** as the production XGBoost model but explores
neural network architectures via systematic hyperparameter grid search.

**This module is completely independent** — it does NOT modify any existing backend,
frontend, or service code.

## Architecture

```
eda/deep_learning/
├── config.py              # Central configuration (paths, grid space, hyperparams)
├── dataset_loader.py      # Fetch UCI Obesity Dataset (id=544)
├── preprocessing.py       # Feature engineering, scaling, train/val/test split
├── build_models.py        # MLP builder (configurable layers, activation, opt, reg)
├── train_models.py        # Grid search engine with callbacks
├── evaluate_models.py     # Test set evaluation (accuracy, F1, ROC-AUC, confusion matrix)
├── save_best_model.py     # Artifact saver (model, scaler, encoder, metrics)
├── inference.py           # Load saved model and predict on new data
├── run_pipeline.py        # Main orchestrator (runs full pipeline end-to-end)
├── README.md              # This file
└── output/                # Generated artifacts (created at runtime)
    ├── best_model.h5
    ├── history.pkl
    ├── scaler.pkl
    ├── label_encoder.pkl
    ├── metrics.json
    ├── grid_results.csv
    └── best_config.json
```

## Grid Search Space

**24 unique architectures** = 3 layer configs × 2 optimizers × 2 activations × 2 regularizers

| Dimension         | Values                        |
|-------------------|-------------------------------|
| Hidden Layers     | 1 [128], 2 [256,128], 3 [512,256,128] |
| Optimizer         | Adam, RMSprop                 |
| Activation        | ReLU, LeakyReLU (α=0.1)      |
| Regularization    | Dropout (0.3), BatchNorm      |

## Callbacks

- **EarlyStopping**: monitor `val_accuracy`, patience=20, restore best weights
- **ReduceLROnPlateau**: monitor `val_loss`, factor=0.5, patience=10
- **ModelCheckpoint**: save best validation accuracy

## Selection Criterion

Best model = **highest validation accuracy** after training.

## How to Run

```bash
# Full pipeline (24 models, ~15-30 min depending on hardware)
python eda/deep_learning/run_pipeline.py

# Quick test (3 models, ~2-3 min)
python eda/deep_learning/run_pipeline.py --quick
```

## Inference

```python
from eda.deep_learning.inference import load_artifacts, predict

artifacts = load_artifacts("eda/deep_learning/output/")
result = predict(artifacts, {
    "Age": 25, "Gender": 1, "Height": 1.75, "Weight": 80.0,
    "SMOKE": 0, "FAF": 1.0, "BMI": 26.12,
    "family_history": 1, "FAVC": 1, "FCVC": 3.0, "CH2O": 2.0,
})
print(result["predicted_class"], result["confidence"])
```

## Dependencies

```
tensorflow >= 2.15
scikit-learn
pandas
numpy
ucimlrepo
```

## Saved Artifacts

| File                  | Description                              |
|-----------------------|------------------------------------------|
| `best_model.h5`       | Keras model (architecture + weights)     |
| `history.pkl`         | Training history (loss, accuracy curves) |
| `scaler.pkl`          | Fitted StandardScaler                    |
| `label_encoder.pkl`   | Fitted LabelEncoder                      |
| `metrics.json`        | Test set metrics (acc, F1, AUC, CM)      |
| `grid_results.csv`    | All 24 configs ranked by val_accuracy    |
| `best_config.json`    | Hyperparameters of the winning model     |
