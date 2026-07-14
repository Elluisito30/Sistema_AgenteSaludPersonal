
# Metodología Científica: Artículo sobre Predicción de Nivel de Obesidad con MLP

---

## 1. Pregunta de investigación
¿Es posible predecir de manera precisa el nivel de obesidad de individuos a partir de variables demográficas, hábitos alimentarios y actividad física utilizando una Red Neuronal Multicapa (MLP), y supera el rendimiento de modelos tradicionales de Machine Learning como Random Forest y XGBoost?

---

## 2. Objetivo general
Desarrollar y validar una Red Neuronal Multicapa (MLP) para la predicción del nivel de obesidad (7 categorías) basada en variables del dataset UCI Obesity, y comparar su rendimiento con modelos de referencia.

---

## 3. Objetivos específicos
1. Realizar preprocesamiento y limpieza del dataset UCI Obesity.
2. Implementar una MLP con arquitectura óptima para la clasificación de niveles de obesidad.
3. Comparar el rendimiento de la MLP con modelos baseline (Random Forest, XGBoost, Regresión Logística).
4. Evaluar la robustez de los modelos utilizando validación cruzada y pruebas estadísticas.
5. Proporcionar una estrategia para la integración del modelo entrenado en el sistema Health AI.

---

## 4. Hipótesis nula y alternativa
- **Hipótesis nula (H₀)**: El rendimiento de la MLP en la predicción del nivel de obesidad no es significativamente mejor que el de los modelos de referencia (Random Forest y XGBoost).
- **Hipótesis alternativa (H₁)**: El rendimiento de la MLP en la predicción del nivel de obesidad es significativamente mejor que el de los modelos de referencia (Random Forest y XGBoost).

---

## 5. Variables independientes
Las variables independientes del estudio son las 16 variables predictoras del dataset:
| Variable | Tipo |
| -------- | ---- |
| `Age` | Numérica continua |
| `Gender` | Binaria |
| `Height` | Numérica continua |
| `Weight` | Numérica continua |
| `family_history_with_overweight` | Binaria |
| `FAVC` | Binaria |
| `FCVC` | Numérica discreta |
| `NCP` | Numérica discreta |
| `CAEC` | Categórica (4 valores) |
| `SMOKE` | Binaria |
| `CH2O` | Numérica continua |
| `SCC` | Binaria |
| `FAF` | Numérica discreta |
| `TUE` | Numérica discreta |
| `CALC` | Categórica (4 valores) |
| `MTRANS` | Categórica (5 valores) |
- **Variable derivada**: `BMI` = `Weight / (Height²)` (adicional para mejorar el rendimiento)

---

## 6. Variable dependiente
- `NObeyesdad`: Nivel de obesidad (categoría ordinal con 7 clases):
  1. Insufficient_Weight
  2. Normal_Weight
  3. Overweight_Level_I
  4. Overweight_Level_II
  5. Obesity_Type_I
  6. Obesity_Type_II
  7. Obesity_Type_III

---

## 7. Diseño experimental
El diseño del estudio es **descriptivo, observacional y transversal** (utiliza datos secundarios del dataset UCI Obesity). Los pasos del diseño experimental son:
1. **Adquisición de datos**: Obtener el dataset desde el UCI Machine Learning Repository (id=544).
2. **Preprocesamiento de datos**:
   - Codificar variables binarias usando LabelEncoder.
   - Codificar variables categóricas usando OneHotEncoder (drop first).
   - Normalizar variables numéricas usando StandardScaler.
   - Calcular la variable derivada BMI.
3. **División de datos**:
   - Hold-out Test (15%): 316 registros, estratificado, se reserva al inicio y NO se usa en entrenamiento ni cross-validation.
   - Train-Val (85%): 1,795 registros, usado para Repeated Stratified K-Fold Cross Validation.
4. **Entrenamiento y validación cruzada**:
   - Validación Cruzada Estratificada K-Fold repetida (5 repeticiones x 10 folds = 50 folds totales) sobre el conjunto Train-Val.
   - Entrenar modelos baseline y la MLP en cada fold.
   - Early Stopping para la MLP en cada fold.
5. **Evaluación final**:
   - Entrenar modelos finalistas en todo el conjunto Train-Val.
   - Medir métricas de evaluación en el Hold-out Test set.
   - Realizar pruebas estadísticas de comparación usando los resultados de Cross Validation.

---

## 8. Arquitectura recomendada de la MLP
| Parámetro | Valor |
| --------- | ----- |
| Capa de entrada | Dinámica: dependiente del preprocesamiento (incluye variables originales, derivada BMI y variables codificadas one-hot) |
| Capas ocultas | 3 capas ocultas con: 64, 32 y 16 neuronas respectivamente |
| Función de activación (capas ocultas) | ReLU (Rectified Linear Unit) |
| Regularización | Dropout (15%) en cada capa oculta para evitar sobreajuste |
| Capa de salida | 7 neuronas (una por cada clase de nivel de obesidad) |
| Función de activación (salida) | Softmax |
| Optimización | Adam (tasa de aprendizaje inicial: 0.001) |
| Función de pérdida | Sparse Categorical Crossentropy |
| Épocas de entrenamiento | Máximo 300, con Early Stopping (patience=20, monitoreando val_loss, restore_best_weights=True) |
| Batch size | 32 |

---

## 9. Modelos de comparación (baseline)
Se seleccionan 3 modelos de Machine Learning tradicionales como baseline para la comparación:
1. **Regresión Logística Multinomial**: Modelo lineal para clasificación multiclase.
2. **Random Forest**: Ensemble de árboles de decisión (100 estimadores).
3. **XGBoost**: Gradient boosting con árboles de decisión (100 estimadores).

---

## 10. Métricas de evaluación
Dado que el problema es una clasificación multiclase con distribución relativamente balanceada, se utilizarán las siguientes métricas:
1. **Exactitud (Accuracy)**: Porcentaje de predicciones correctas.
2. **Balanced Accuracy**: Promedio de recall por clase, robusta a desbalance de clases.
3. **Cohen's Kappa**: Medida de acuerdo entre predicciones y valores reales, corrigiendo por azar.
4. **F1-Score Macro**: Promedio de F1-score por clase sin ponderar por soporte.
5. **F1-Score Weighted**: Promedio de F1-score por clase ponderado por soporte.
6. **ROC-AUC Multiclase (One-vs-Rest, OvR)**: Área bajo la curva ROC para clasificación multiclase.
7. **Matriz de confusión**: Para analizar errores específicos de clasificación.

---

## 11. Pruebas estadísticas robustas para comparar modelos
Para validar la hipótesis alternativa, se utilizarán las siguientes pruebas estadísticas sobre los resultados de la validación cruzada repetida (usando F1-Score Macro como métrica principal):
1. **Prueba de Friedman**: Prueba no paramétrica para comparar el rendimiento de múltiples modelos (Regresión Logística, Random Forest, XGBoost, MLP) en múltiples folds.
2. **Prueba post-hoc de Nemenyi**: Si la prueba de Friedman es estadísticamente significativa (p < 0.05), se realiza para identificar qué pares de modelos tienen diferencias significativas en su rendimiento.

---

## 12. Estrategia de validación cruzada
Se utilizará **Repeated Stratified K-Fold Cross Validation** con los siguientes parámetros:
- **Número de folds (K)**: 10
- **Número de repeticiones**: 5
- **Total de folds evaluados**: 50
- **Estratificación**: Mantiene la distribución de la variable objetivo en cada fold, para asegurar representatividad.
- **Early Stopping**: Durante el entrenamiento de la MLP en cada fold, se usa la porción de validación para detener el entrenamiento temprano (patience=20, restore_best_weights=True) y evitar sobreajuste.
- **Hold-out Test**: Conjunto de test reservado al inicio (15% de los datos), que se usa sólo para la evaluación final de los modelos entrenados en todo el conjunto Train-Val.

---

## 13. Amenazas a la validez
Se identifican las siguientes amenazas a la validez del estudio:
1. **Validez interna**:
   - **Datos sintéticos**: El 77% del dataset fue generado sintéticamente (SMOTE + Weka), lo que puede afectar la generalización a datos reales.
   - **Sobreajuste**: La MLP puede sobreajustarse a los datos de entrenamiento.
2. **Validez externa**:
   - **Población limitada**: El dataset incluye solo individuos de México, Perú y Colombia, lo que puede limitar la generalización a otras poblaciones.
3. **Validez de constructo**:
   - **Variables no disponibles**: El dataset no incluye variables como horas de sueño, estrés o consumo de macronutrientes, que son relevantes para el sistema Health AI.

---

## 14. Limitaciones del estudio
1. El dataset contiene un 77% de datos sintéticos, lo que puede reducir la representatividad de la población real.
2. No hay datos temporales (longitudinales), lo que impide estudiar la evolución del nivel de obesidad a lo largo del tiempo.
3. Faltan variables importantes del sistema Health AI (horas de sueño, estrés, consumo de macronutrientes).
4. El estudio se limita a la clasificación de niveles de obesidad, no a la predicción de recomendaciones personalizadas.

---

## 15. Estrategia para integrar el modelo entrenado en el sistema Health AI
Para integrar la MLP en el sistema Health AI, se recomienda la siguiente estrategia:
1. **Exportar el modelo**:
   - Guardar el modelo entrenado en formato HDF5 (.h5) o TensorFlow SavedModel.
   - Guardar el pipeline de preprocesamiento (encoders, scaler) como un objeto pickle o usando `joblib`.
2. **Integrar en el backend**:
   - Crear un nuevo endpoint en el backend FastAPI (`/api/v1/predict-obesity`) que reciba los datos del usuario y devuelva la predicción del nivel de obesidad.
   - Cargar el modelo y el pipeline de preprocesamiento al iniciar el backend.
3. **Modificar el frontend**:
   - Agregar una nueva pantalla en el frontend React para la predicción de nivel de obesidad.
   - Enviar los datos del usuario (perfil de salud) al endpoint del backend.
   - Mostrar la predicción y la confianza al usuario.
4. **Actualizar Docker Compose**:
   - Añadir la carpeta `models` al volumen del contenedor backend.
5. **Validación y prueba**:
   - Probar la integración con datos de prueba del sistema Health AI.
   - Monitorizar el rendimiento del modelo en producción.
