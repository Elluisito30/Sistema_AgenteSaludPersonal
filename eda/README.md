
# Experiment Directory for Obesity Prediction

This directory contains all the files for the scientific experiment on obesity level prediction using an MLP.

## Directory Structure
- `src/`: Contains Python scripts for preprocessing and training/evaluation.
  - `preprocessing.py`: Preprocessing script.
  - `train_eval.py`: Training and evaluation script.
- `models/`: Directory to save trained models, preprocessors, and results.
- `INFORME_EDA.md`: Exploratory Data Analysis report.
- `METODOLOGIA_ARTICULO.md`: Full methodology for the scientific article.
- `eda_obesity.py`: Initial EDA script.

## How to Run
1. Install dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```
2. Run the training and evaluation script:
   ```bash
   cd src
   python train_eval.py
   ```

## Results
- Results will be saved in `models/`:
  - `results.csv`: Table of evaluation metrics for all models.
  - `confusion_matrix_mlp.png`: Confusion matrix for the MLP model.
  - `mlp_training_history.png`: Training/validation loss and accuracy for MLP.
  - Trained models and preprocessors.
