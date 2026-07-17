"""
ImageAnalyzer — stub preparado para conexion futura con modelo de vision.
Actualmente retorna estimaciones simuladas claramente identificadas.
"""


class ImageAnalyzer:
    """Analiza imagenes de comida y retorna foods detectados.
    
    Arquitectura desacoplada:
    - Acepta bytes de imagen o URL
    - Retorna lista de food items con bounding boxes simulados
    - Preparado para conectar un modelo de vision (YOLO, etc.)
    """

    def analyze(self, image_bytes: bytes = None, image_url: str = None) -> dict:
        if image_bytes is None and image_url is None:
            return {"success": False, "error": "No image provided"}

        return {
            "success": True,
            "simulated": True,
            "detection_method": "placeholder",
            "items_detected": [
                {
                    "name": "food_item_detected",
                    "confidence": 0.0,
                    "bounding_box": {"x": 0, "y": 0, "w": 100, "h": 100},
                    "note": "Estimacion IA — modelo de vision no conectado"
                }
            ]
        }
