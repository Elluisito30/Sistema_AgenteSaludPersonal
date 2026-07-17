"""
NutritionEstimator — calcula valores nutricionales estimados.
Preparado para conectarse a una base de datos nutricional o modelo de IA.
"""


class NutritionEstimator:
    """Estima calorias y macro/micronutrientes de un alimento.
    
    Arquitectura desacoplada:
    - Acepta nombre del alimento + cantidad estimada
    - Retorna desglose nutricional simulado
    - Preparado para conectar con USDA FoodData Central, OpenFoodFacts, etc.
    """

    COMMON_FOODS = {
        "arroz": {"calories": 130, "protein": 2.7, "carbs": 28, "fats": 0.3, "fiber": 0.4},
        "pollo": {"calories": 165, "protein": 31, "carbs": 0, "fats": 3.6, "fiber": 0},
        "huevo": {"calories": 155, "protein": 13, "carbs": 1.1, "fats": 11, "fiber": 0},
        "ensalada": {"calories": 20, "protein": 1.5, "carbs": 3.5, "fats": 0.2, "fiber": 1.5},
        "pan": {"calories": 265, "protein": 9, "carbs": 49, "fats": 3.2, "fiber": 2.7},
        "leche": {"calories": 61, "protein": 3.2, "carbs": 4.8, "fats": 3.3, "fiber": 0},
        "fruta": {"calories": 52, "protein": 0.3, "carbs": 14, "fats": 0.2, "fiber": 2.4},
        "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fats": 1.1, "fiber": 1.8},
        "verdura": {"calories": 25, "protein": 2, "carbs": 4, "fats": 0.3, "fiber": 2},
        "carne": {"calories": 250, "protein": 26, "carbs": 0, "fats": 15, "fiber": 0},
        "pescado": {"calories": 206, "protein": 22, "carbs": 0, "fats": 12, "fiber": 0},
        "sopa": {"calories": 50, "protein": 3, "carbs": 7, "fats": 1, "fiber": 1},
        "cereal": {"calories": 379, "protein": 7, "carbs": 84, "fats": 1, "fiber": 3},
        "yogurt": {"calories": 59, "protein": 3.5, "carbs": 4.7, "fats": 3.3, "fiber": 0},
        "aguacate": {"calories": 160, "protein": 2, "carbs": 9, "fats": 15, "fiber": 7},
        "frijoles": {"calories": 127, "protein": 8.7, "carbs": 22.8, "fats": 0.5, "fiber": 7.4},
    }

    def estimate(self, food_name: str, portion_grams: float = 200.0) -> dict:
        name_lower = food_name.lower().strip()
        base = self.COMMON_FOODS.get(name_lower)

        if base is None:
            base = {"calories": 150, "protein": 8, "carbs": 20, "fats": 5, "fiber": 2}

        multiplier = portion_grams / 200.0

        return {
            "food_name": food_name,
            "portion_grams": portion_grams,
            "estimated": True,
            "estimation_source": "placeholder_simulation",
            "nutrients": {
                "calories": round(base["calories"] * multiplier, 1),
                "protein_g": round(base["protein"] * multiplier, 1),
                "carbs_g": round(base["carbs"] * multiplier, 1),
                "fats_g": round(base["fats"] * multiplier, 1),
                "fiber_g": round(base["fiber"] * multiplier, 1),
            }
        }
