
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print("SCRIPT_DIR:", SCRIPT_DIR)
print("os.path.dirname(SCRIPT_DIR):", os.path.dirname(SCRIPT_DIR))
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'models')
print("MODELS_DIR:", MODELS_DIR)
os.makedirs(MODELS_DIR, exist_ok=True)
print("Directory created/exists:", os.path.exists(MODELS_DIR))
