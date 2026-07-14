# Deep Learning Validation Module

## Overview

Scientific validation suite for the trained Neural Network (MLP) obesity classifier.

**This module is read-only** — it only reads from `output/` artifacts and the original UCI dataset. It never retrains any model.

## Architecture

```
validation/
├── confusion_analysis.py      # Normalized confusion matrix + heatmap
├── roc_analysis.py            # OvR, Macro, Micro ROC curves + AUC
├── calibration_analysis.py    # Calibration curves + Brier Score
├── bootstrap_validation.py    # 95% Bootstrap CI for Accuracy, F1, AUC
├── statistical_comparison.py  # XGBoost vs NN: Wilcoxon, McNemar, DeLong
├── precision_recall.py        # Per-class Precision-Recall curves + AP
├── generate_report.py         # Orchestrator — runs all analyses + generates report
├── README.md                  # This file
│
└── (generated at runtime)
    ├── confusion_matrix.png
    ├── roc_curves.png
    ├── calibration_curve.png
    ├── precision_recall.png
    ├── validation_metrics.json
    ├── comparison_results.csv
    └── validation_report.md
```

## How to Run

```bash
# Full validation pipeline
python eda/deep_learning/validation/generate_report.py
```

## Requirements

- Trained model in `eda/deep_learning/output/` (best_model.h5, scaler.pkl, label_encoder.pkl, metrics.json)
- XGBoost model in `eda/models/xgb_11f.bin` + `le_target_11f.pkl`
- Packages: tensorflow, scikit-learn, xgboost, scipy, matplotlib, seaborn, pandas, numpy

## Analyses Performed

| # | Analysis | Output | Description |
|---|----------|--------|-------------|
| 1 | Confusion Matrix | `confusion_matrix.png` | Normalized row-wise heatmap |
| 2 | ROC Curves | `roc_curves.png` | OvR per-class + Macro + Micro |
| 3 | Precision-Recall | `precision_recall.png` | Per-class PR curves + AP |
| 4 | Calibration | `calibration_curve.png` | Reliability diagram + Brier Score |
| 5 | Bootstrap | (in JSON) | 95% CI for Accuracy, F1, AUC |
| 6 | Comparison | `comparison_results.csv` | Wilcoxon, McNemar, DeLong |
| 7 | Report | `validation_report.md` | Academic-format report |
