# Informe de Validación del Experimento

## 1. Resumen del Experimento
El objetivo del experimento es evaluar y comparar el rendimiento de cuatro modelos de clasificación para la predicción de niveles de obesidad:
- Regresión Logística
- Random Forest
- XGBoost
- Red Neuronal (MLP)

El experimento utiliza el conjunto de datos de Obesidad de la UCI (2111 registros, 7 clases). Se emplea:
- División inicial en Hold-Out Test (15%) y Train-Val (85%)
- Validación cruzada repetida estratificada 5x10 (5 repeticiones, 10 folds)
- Preprocesamiento con ajuste solo en el conjunto de entrenamiento de cada fold para evitar fugas de datos
- Prueba estadística de Friedman y (si es necesario) prueba post-hoc de Nemenyi

---

## 2. Modificaciones Realizadas en el Código
Para la ejecución correcta del experimento, se realizaron las siguientes correcciones en el código:

1. **Fix 1: Eliminación de `multi_class` en LogisticRegression**
   - **Archivo**: [train_eval.py](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/src/train_eval.py#L138)
   - **Justificación**: En versiones modernas de scikit-learn, el parámetro `multi_class` está obsoleto y el modelo selecciona automáticamente la estrategia adecuada.
   - **Cambio**: Eliminado el argumento `multi_class='multinomial'` en las instancias de `LogisticRegression`.

2. **Fix 2: Manejo de categorías desconocidas en OneHotEncoder**
   - **Archivo**: [preprocessing.py](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/src/preprocessing.py#L61)
   - **Justificación**: Al hacer validación cruzada, es posible que el fold de validación contenga categorías no presentes en el fold de entrenamiento, lo cual generaba un error.
   - **Cambio**: Añadido `handle_unknown='ignore'` en el `OneHotEncoder` del `ColumnTransformer`.

3. **Fix 3: Rutas absolutas para guardar archivos**
   - **Archivo**: [train_eval.py](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/src/train_eval.py#L14-L18)
   - **Justificación**: El uso de rutas relativas generaba directorios anidados incorrectos cuando el script se ejecutaba desde diferentes ubicaciones.
   - **Cambio**: Añadido código para obtener la ruta del script y usar rutas absolutas al directorio `eda/models/`.

---

## 3. Resultados de la Evaluación
### Resultados del Hold-Out Test
| Modelo                  | Accuracy | Balanced Accuracy | Cohen's Kappa | F1 Macro | F1 Weighted | ROC AUC OvR |
|-------------------------|----------|-------------------|---------------|----------|-------------|-------------|
| Regresión Logística     | 0.8833   | 0.8789            | 0.8636        | 0.8773   | 0.8810      | 0.9840      |
| Random Forest           | 0.9558   | 0.9548            | 0.9484        | 0.9560   | 0.9573      | 0.9951      |
| XGBoost                 | 0.9653   | 0.9650            | 0.9595        | 0.9648   | 0.9654      | 0.9990      |
| MLP                     | 0.9527   | 0.9512            | 0.9447        | 0.9506   | 0.9523      | 0.9983      |

### Prueba Estadística de Friedman
- Estadístico Friedman: 5.4000
- Valor p: 0.1447
- **Conclusión**: No se rechaza la hipótesis nula (p ≥ 0.05), por lo que no hay diferencias estadísticamente significativas entre los modelos con este subconjunto de datos.

---

## 4. Archivos Generados
Todos los archivos del experimento se guardan en el directorio `eda/models/`:
- [cv_results.csv](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/cv_results.csv): Resultados de cada fold en la validación cruzada
- [holdout_test_results.csv](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/holdout_test_results.csv): Resultados en el conjunto de hold-out test
- [statistical_results.csv](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/statistical_results.csv): Resultados de la prueba de Friedman
- [logreg.pkl](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/logreg.pkl): Modelo de Regresión Logística entrenado
- [rf.pkl](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/rf.pkl): Modelo Random Forest entrenado
- [xgb.json](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/xgb.json): Modelo XGBoost entrenado
- [obesity_mlp.h5](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/obesity_mlp.h5): Modelo MLP entrenado
- [preprocessor.pkl](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/preprocessor.pkl): Preprocesador ajustado
- [binary_encoders.pkl](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/binary_encoders.pkl): Codificadores para variables binarias
- [le_target.pkl](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/le_target.pkl): Codificador para la variable objetivo
- [confusion_matrix_mlp_test.png](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/confusion_matrix_mlp_test.png): Matriz de confusión del MLP en el hold-out test
- [mlp_final_training_history.png](file:///c:/Users/user/Documents/GitHub/Sistema_AgenteSaludPersonal/eda/models/mlp_final_training_history.png): Curvas de entrenamiento del MLP final

---

## 5. Conclusiones
- El pipeline de experimento funciona correctamente después de las correcciones.
- Los modelos de Random Forest y XGBoost muestran el mejor rendimiento en este conjunto de datos.
- La calidad metodológica es alta: se evita la fuga de datos, se usa validación cruzada repetida y pruebas estadísticas para la comparación de modelos.
