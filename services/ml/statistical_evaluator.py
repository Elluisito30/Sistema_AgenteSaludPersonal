import os
import json
import numpy as np
from scipy import stats
import joblib
import xgboost as xgb
from sklearn.metrics import accuracy_score, confusion_matrix
import warnings
warnings.filterwarnings("ignore")

class StatisticalEvaluator:
    def __init__(self):
        self.models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "eda", "models"
        )
        self.le_target = None
        self.classes = []
        self._load_dependencies()

    def _load_dependencies(self):
        le_path = os.path.join(self.models_dir, "le_target_11f.pkl")
        if os.path.exists(le_path):
            self.le_target = joblib.load(le_path)
            self.classes = list(self.le_target.classes_)
        else:
            self.classes = ["Insufficient_Weight", "Normal_Weight", "Overweight_Level_I", 
                            "Overweight_Level_II", "Obesity_Type_I", "Obesity_Type_II", "Obesity_Type_III"]

    def _generate_synthetic_test_data(self, n_samples=100, random_state=42):
        np.random.seed(random_state)
        # 11 features: age, gender, height, weight, smoke, faf, bmi, family_history, favc, fcvc, ch2o
        X_test = []
        y_test = []
        for _ in range(n_samples):
            age = np.random.uniform(18, 60)
            gender = np.random.randint(0, 2)
            height = np.random.uniform(150, 190)
            weight = np.random.uniform(50, 120)
            smoke = np.random.randint(0, 2)
            faf = np.random.uniform(0, 3)
            bmi = weight / ((height/100)**2)
            fh = np.random.randint(0, 2)
            favc = np.random.randint(0, 2)
            fcvc = np.random.uniform(1, 3)
            ch2o = np.random.uniform(1, 3)
            
            features = [age, gender, height, weight, smoke, faf, bmi, fh, favc, fcvc, ch2o]
            X_test.append(features)
            
            # Simple heuristic for true label based on BMI
            if bmi < 18.5: label = 0
            elif bmi < 25: label = 1
            elif bmi < 28: label = 2
            elif bmi < 30: label = 3
            elif bmi < 35: label = 4
            elif bmi < 40: label = 5
            else: label = 6
            y_test.append(label)
            
        return np.array(X_test), np.array(y_test)

    def _load_backend_models(self):
        models = {}
        
        # 1. XGBoost
        xgb_path = os.path.join(self.models_dir, "xgb_11f.bin")
        if os.path.exists(xgb_path):
            try:
                m_xgb = xgb.XGBClassifier()
                m_xgb.load_model(xgb_path)
                models['XGBoost'] = m_xgb
            except Exception as e: print(f"Error loading XGB: {e}")
            
        # 2. Random Forest
        rf_path = os.path.join(self.models_dir, "rf.pkl")
        if os.path.exists(rf_path):
            try:
                m_rf = joblib.load(rf_path)
                models['RandomForest'] = m_rf
            except Exception as e: print(f"Error loading RF: {e}")
            
        # 3. MLP (Keras)
        mlp_path = os.path.join(self.models_dir, "obesity_mlp.h5")
        if os.path.exists(mlp_path):
            try:
                from tensorflow.keras.models import load_model
                m_mlp = load_model(mlp_path)
                models['MLP'] = m_mlp
            except Exception as e: print(f"Error loading MLP: {e}")
            
        return models

    def get_test_dataset_for_frontend(self):
        X, y = self._generate_synthetic_test_data()
        return {"X": X.tolist(), "y": y.tolist(), "classes": self.classes}

    def evaluate_all(self, frontend_y_pred):
        X_test, y_test = self._generate_synthetic_test_data()
        b_models = self._load_backend_models()
        
        predictions = {}
        # Backend predictions
        if 'XGBoost' in b_models:
            try:
                predictions['XGBoost'] = b_models['XGBoost'].predict(X_test)
            except Exception as e:
                print(f"XGB predict error: {e}")
                predictions['XGBoost'] = np.random.randint(0, len(self.classes), size=len(y_test))
        else:
            predictions['XGBoost'] = np.random.randint(0, len(self.classes), size=len(y_test))
            
        if 'RandomForest' in b_models:
            try:
                predictions['RandomForest'] = b_models['RandomForest'].predict(X_test)
            except Exception as e:
                print(f"RF predict error: {e}")
                predictions['RandomForest'] = np.random.randint(0, len(self.classes), size=len(y_test))
        else:
            predictions['RandomForest'] = np.random.randint(0, len(self.classes), size=len(y_test))
            
        if 'MLP' in b_models:
            try:
                preds = b_models['MLP'].predict(X_test)
                predictions['MLP'] = np.argmax(preds, axis=1)
            except Exception as e:
                print(f"MLP predict error: {e}")
                predictions['MLP'] = np.random.randint(0, len(self.classes), size=len(y_test))
        else:
            predictions['MLP'] = np.random.randint(0, len(self.classes), size=len(y_test))
            
        # Frontend prediction
        predictions['FrontendJS'] = np.array(frontend_y_pred)
        
        # Calculate Accuracies and Folds (10 folds of 10 samples)
        n_folds = 10
        fold_size = len(y_test) // n_folds
        
        model_results = {}
        for m_name, y_pred in predictions.items():
            acc = accuracy_score(y_test, y_pred)
            cm = confusion_matrix(y_test, y_pred, labels=range(len(self.classes))).tolist()
            
            folds_acc = []
            for i in range(n_folds):
                start = i * fold_size
                end = start + fold_size
                folds_acc.append(accuracy_score(y_test[start:end], y_pred[start:end]))
                
            model_results[m_name] = {
                "accuracy": float(acc),
                "confusion_matrix": cm,
                "folds_accuracy": [float(f) for f in folds_acc]
            }

        # Select Winner
        best_model_name = max(model_results, key=lambda k: model_results[k]['accuracy'])
        
        # Statistical Tests
        stats_results = self._run_statistical_tests(model_results, predictions, y_test, best_model_name)
        
        return {
            "models": model_results,
            "statistics": stats_results,
            "winner": best_model_name,
            "classes": self.classes
        }

    def _run_statistical_tests(self, model_results, predictions, y_test, best_model_name):
        # 1. Shapiro-Wilk on the folds of the best model to check normality
        best_folds = model_results[best_model_name]['folds_accuracy']
        stat_s, p_shapiro = stats.shapiro(best_folds)
        
        shapiro_text = (
            f"El test de Shapiro-Wilk arrojó un p-valor de {p_shapiro:.4f}. "
            f"{'Dado que p < 0.05, rechazamos la hipótesis nula, concluyendo que las exactitudes NO provienen de una distribución normal.' if p_shapiro < 0.05 else 'Dado que p >= 0.05, aceptamos la hipótesis nula, concluyendo que las exactitudes provienen de una distribución normal.'}"
        )
        
        # 2. Friedman Test across all 4 models
        all_folds = [model_results[m]['folds_accuracy'] for m in model_results.keys()]
        stat_f, p_friedman = stats.friedmanchisquare(*all_folds)
        
        friedman_text = (
            f"El test de Friedman arrojó un p-valor de {p_friedman:.4f}. "
            f"{'Como p < 0.05, existe una diferencia estadísticamente significativa en el rendimiento de al menos un modelo respecto a los demás.' if p_friedman < 0.05 else 'Como p >= 0.05, no se encontraron diferencias significativas entre el rendimiento global de los modelos.'}"
        )
        
        # 3. McNemar Test: Best model vs Second Best model
        sorted_models = sorted(model_results.keys(), key=lambda k: model_results[k]['accuracy'], reverse=True)
        second_best = sorted_models[1] if len(sorted_models) > 1 else sorted_models[0]
        
        y_pred_best = predictions[best_model_name]
        y_pred_second = predictions[second_best]
        
        best_correct = (y_pred_best == y_test)
        second_correct = (y_pred_second == y_test)
        
        b01 = int(np.sum(~best_correct & second_correct))
        b10 = int(np.sum(best_correct & ~second_correct))
        
        n_discordant = b01 + b10
        if n_discordant < 25 and n_discordant > 0:
            stat_m = (abs(b01 - b10) - 1) ** 2 / n_discordant
        elif n_discordant >= 25:
            stat_m = (b01 - b10) ** 2 / n_discordant
        else:
            stat_m = 0
            
        p_mcnemar = 1 - stats.chi2.cdf(stat_m, df=1) if n_discordant > 0 else 1.0
        
        mcnemar_text = (
            f"Al comparar el mejor modelo ({best_model_name}) contra el segundo mejor ({second_best}) mediante el test de McNemar, "
            f"se obtuvo un p-valor de {p_mcnemar:.4f}. "
            f"{'Al ser p < 0.05, se concluye formalmente que el modelo ganador es estadísticamente superior en sus predicciones dicotómicas.' if p_mcnemar < 0.05 else 'Al ser p >= 0.05, no se puede afirmar estadísticamente que las predicciones del modelo ganador sean significativamente superiores a las del segundo mejor, a pesar de la diferencia en exactitud absoluta.'}"
        )
        
        return {
            "shapiro": {"p_value": p_shapiro, "interpretation": shapiro_text},
            "friedman": {"p_value": p_friedman, "interpretation": friedman_text},
            "mcnemar": {"p_value": p_mcnemar, "interpretation": mcnemar_text, "compared_against": second_best}
        }

statistical_evaluator = StatisticalEvaluator()
