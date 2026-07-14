import xgboost as xgb
import json
import os

model = xgb.XGBClassifier()
model.load_model(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'xgb_11f.bin'))

feature_names = ['Age', 'Gender', 'Height', 'Weight', 'SMOKE', 'FAF', 'BMI', 'family_history', 'FAVC', 'FCVC', 'CH2O']
importances = model.feature_importances_

display_names = {
    'Age': 'Edad', 'Gender': 'Sexo', 'Height': 'Estatura',
    'Weight': 'Peso', 'SMOKE': 'Tabaquismo', 'FAF': 'Actividad física',
    'BMI': 'IMC', 'family_history': 'Antecedentes familiares',
    'FAVC': 'Comida chatarra', 'FCVC': 'Consumo de vegetales',
    'CH2O': 'Consumo de agua'
}

result = []
for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
    result.append({'feature': name, 'importance': round(float(imp), 4), 'display_name': display_names[name]})

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'importance.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

for item in result:
    print(f"  {item['display_name']:25s} {item['importance']:.4f}")
print(f"\nSaved: {out_path}")
