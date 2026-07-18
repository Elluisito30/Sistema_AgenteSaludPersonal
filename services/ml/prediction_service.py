"""
ML Prediction Service — Singleton que carga el modelo XGBoost (11 features)
y expone predicciones de obesidad.

Features usadas (disponibles en health_profiles):
  Age, Gender, Height, Weight, SMOKE, FAF, BMI,
  family_history, FAVC, FCVC, CH2O

Modelo: xgb_11f.bin (entrenado con 11 features, ~99% accuracy)
"""

import os
import time
import json
import joblib

# Mapa activity_level -> FAF (0-3)
ACTIVITY_TO_FAF = {
    "sedentary": 0,
    "light": 1,
    "moderate": 2,
    "active": 3,
    "very_active": 3,
}


class PredictionService:
    """
    Singleton que gestiona el modelo XGBoost de predicción de obesidad.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.model = None
        self.le_target = None
        self.model_loaded = False
        self._load_artifacts()

    def _get_models_dir(self):
        docker_path = "/app/models"
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "eda", "models"
        )
        if os.path.isdir(docker_path):
            return docker_path
        return local_path

    def _load_artifacts(self):
        try:
            import xgboost as xgb
        except ImportError as e:
            print(f"XGBoost dependency not installed: {e}")
            return

        models_dir = self._get_models_dir()
        target_path = os.path.join(models_dir, "le_target_11f.pkl")

        if not os.path.isfile(target_path):
            print("Target encoder not found")
            return

        try:
            self.le_target = joblib.load(target_path)
        except Exception as e:
            print(f"Error loading le_target: {e}")
            return

        # Load Config
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json")
        active_model = "XGBoost"
        model_type = "backend"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                active_model = config.get("active_model", "XGBoost")
                model_type = config.get("type", "backend")

        self.active_model_name = active_model
        self.model_type = model_type
        
        if model_type == "frontend":
            self.model_loaded = True
            print(f"ML Active model is Frontend JS. Backend will wait for client inference.")
            return

        # Load specific backend model
        try:
            if active_model == "XGBoost":
                model_path = os.path.join(models_dir, "xgb_11f.bin")
                self.model = xgb.XGBClassifier()
                self.model.load_model(model_path)
            elif active_model == "RandomForest":
                model_path = os.path.join(models_dir, "rf.pkl")
                self.model = joblib.load(model_path)
            elif active_model == "MLP":
                from tensorflow.keras.models import load_model
                model_path = os.path.join(models_dir, "obesity_mlp.h5")
                self.model = load_model(model_path)
                
            self.model_loaded = True
            print(f"ML model loaded: {active_model} | classes={list(self.le_target.classes_)}")
        except Exception as e:
            print(f"Error loading ML model {active_model}: {e}")
            self.model_loaded = False

    def predict_obesity(
        self,
        age: int,
        gender: str,
        height_cm: float,
        weight_kg: float,
        smokes: bool,
        activity_level: str,
        family_history: bool = False,
        favc: str = "Sometimes",
        fcvc: float = 2.0,
        ch2o: float = 2.0,
    ) -> dict:
        """
        Predice la clase de obesidad usando el modelo XGBoost (11 features).
        """
        if not self.model_loaded:
            return {
                "predicted_class": None,
                "confidence": 0.0,
                "probabilities": {},
                "model_used": "none",
                "inference_time_ms": 0.0,
            }

        if getattr(self, 'model_type', 'backend') == "frontend":
            return {
                "predicted_class": None,
                "confidence": 0.0,
                "probabilities": {},
                "model_used": "FrontendJS",
                "inference_time_ms": 0.0,
                "require_client_inference": True
            }

        t0 = time.time()

        gender_val = 1 if gender == "male" else 0
        smoke_val = 1 if smokes else 0
        faf_val = ACTIVITY_TO_FAF.get(activity_level, 2)
        bmi = weight_kg / ((height_cm / 100) ** 2)
        fh_val = 1 if family_history else 0
        favc_val = 1 if favc == "Always" or favc == "Frequently" else 0
        # fcvc and ch2o are already numeric (1.0-3.0)

        import numpy as np
        features = np.array([[
            float(age),         # Age
            float(gender_val),  # Gender
            float(height_cm),   # Height
            float(weight_kg),   # Weight
            float(smoke_val),   # SMOKE
            float(faf_val),     # FAF
            float(bmi),         # BMI
            float(fh_val),      # family_history
            float(favc_val),    # FAVC
            float(fcvc),        # FCVC
            float(ch2o),        # CH2O
        ]])

        if self.active_model_name == "MLP":
            proba = self.model.predict(features)[0]
            pred_idx = int(np.argmax(proba))
        else:
            pred_idx = int(self.model.predict(features)[0])
            proba = self.model.predict_proba(features)[0]

        predicted_class = self.le_target.classes_[pred_idx]
        confidence = float(proba[pred_idx]) * 100.0

        probabilities = {
            cls: round(float(p) * 100.0, 2)
            for cls, p in zip(self.le_target.classes_, proba)
        }

        inference_ms = (time.time() - t0) * 1000.0

        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 2),
            "probabilities": probabilities,
            "model_used": self.active_model_name,
            "inference_time_ms": round(inference_ms, 2),
        }


prediction_service = PredictionService()
