
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print("SCRIPT_DIR:", SCRIPT_DIR)
MODELS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'eda', 'models')  # Wait! Wait! Oh! Wait! Wait! Because if the test script is in the root, os.path.dirname(SCRIPT_DIR) would be the parent of root! Wait! Wait let's check train_eval.py's SCRIPT_DIR again! Wait train_eval.py is in eda/src/! So os.path.dirname(SCRIPT_DIR) for train_eval.py would be eda/, right? So MODELS_DIR should be os.path.join(os.path.dirname(SCRIPT_DIR), 'models') → eda/models! But why isn't it being created? Let's test with a script in eda/src/!
