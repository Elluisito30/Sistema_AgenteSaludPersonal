"""
FoodAnalysisService — servicio orquestador para analisis de comidas.
Combina ImageAnalyzer + NutritionEstimator en un pipeline unico.
Preparado para conectar un modelo de vision real en el futuro.
"""

from .image_analyzer import ImageAnalyzer
from .nutrition_estimator import NutritionEstimator


class FoodAnalysisService:
    """Orquesta el analisis completo de una comida.
    
    Pipeline:
    1. ImageAnalyzer detecta alimentos en la imagen (simulado por ahora)
    2. NutritionEstimator calcula valores nutricionales
    3. Retorna resultado unificado con flag 'simulated'
    """

    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.nutrition_estimator = NutritionEstimator()

    def analyze_meal(
        self,
        food_name: str = None,
        portion_grams: float = 200.0,
        image_bytes: bytes = None,
        image_url: str = None,
        meal_type: str = "other",
    ) -> dict:
        nutrition_result = None
        detection_result = None

        if food_name:
            nutrition_result = self.nutrition_estimator.estimate(food_name, portion_grams)
        elif image_bytes or image_url:
            detection_result = self.image_analyzer.analyze(
                image_bytes=image_bytes, image_url=image_url
            )
            if detection_result.get("success") and detection_result.get("items_detected"):
                first_item = detection_result["items_detected"][0]
                nutrition_result = self.nutrition_estimator.estimate(
                    first_item.get("name", "unknown"), portion_grams
                )
        else:
            return {
                "success": False,
                "error": "Proporcione food_name o imagen para analizar"
            }

        if nutrition_result is None:
            return {
                "success": False,
                "error": "No se pudo estimar la informacion nutricional"
            }

        return {
            "success": True,
            "simulated": True,
            "simulation_note": (
                "Estimacion IA — modelo de vision artificial no conectado. "
                "Los valores son aproximados y estan claramente identificados."
            ),
            "meal_type": meal_type,
            "detection": detection_result,
            "nutrition": nutrition_result,
        }
