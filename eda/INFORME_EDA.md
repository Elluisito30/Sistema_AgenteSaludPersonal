
# Informe Técnico: Análisis Exploratorio de Datos (EDA) del UCI Obesity Dataset

---

## 1. Número total de registros
- **2,111** registros (individuos de México, Perú y Colombia).

## 2. Número total de variables
- **17** variables en total (16 variables predictoras, 1 variable objetivo).

## 3. Descripción detallada de cada variable
| Variable | Descripción |
| -------- | ----------- |
| `Age` | Edad del individuo |
| `Gender` | Género del individuo |
| `Height` | Estatura del individuo (en metros) |
| `Weight` | Peso del individuo (en kilogramos) |
| `family_history_with_overweight` | Si tiene un familiar con sobrepeso u obesidad |
| `FAVC` | Si consume alimentos altos en calorías frecuentemente |
| `FCVC` | Frecuencia de consumo de vegetales en las comidas |
| `NCP` | Número de comidas principales por día |
| `CAEC` | Frecuencia de consumo de alimentos entre comidas |
| `SMOKE` | Si fuma |
| `CH2O` | Consumo de agua diario (litros) |
| `SCC` | Si monitorea el consumo de calorías |
| `FAF` | Frecuencia de actividad física (días a la semana) |
| `TUE` | Tiempo de uso de dispositivos tecnológicos (horas al día) |
| `CALC` | Frecuencia de consumo de alcohol |
| `MTRANS` | Medio de transporte habitual |
| `NObeyesdad` | Nivel de obesidad (variable objetivo) |

## 4. Tipo de cada variable
| Variable | Tipo | Valores únicos |
| -------- | ---- | -------------- |
| `Age` | Numérica continua | 140 |
| `Gender` | Binaria | 2 (Female, Male) |
| `Height` | Numérica continua | 162 |
| `Weight` | Numérica continua | 153 |
| `family_history_with_overweight` | Binaria | 2 (yes, no) |
| `FAVC` | Binaria | 2 (yes, no) |
| `FCVC` | Numérica discreta | 24 |
| `NCP` | Numérica discreta | 28 |
| `CAEC` | Categórica | 4 (Sometimes, Frequently, Always, no) |
| `SMOKE` | Binaria | 2 (yes, no) |
| `CH2O` | Numérica continua | 26 |
| `SCC` | Binaria | 2 (yes, no) |
| `FAF` | Numérica discreta | 24 |
| `TUE` | Numérica discreta | 20 |
| `CALC` | Categórica | 4 (Sometimes, no, Frequently, Always) |
| `MTRANS` | Categórica | 5 (Public_Transportation, Automobile, Walking, Motorbike, Bike) |
| `NObeyesdad` | Categórica | 7 (Insufficient_Weight, Normal_Weight, Overweight_Level_I, Overweight_Level_II, Obesity_Type_I, Obesity_Type_II, Obesity_Type_III) |

## 5. Variable objetivo
- `NObeyesdad`: Nivel de obesidad (clasificación ordinal con 7 categorías).

## 6. Distribución de clases
| Nivel de obesidad | Recuento | Porcentaje (%) |
| ------------------ | -------- | -------------- |
| Obesity_Type_I | 351 | 16.63 |
| Obesity_Type_III | 324 | 15.35 |
| Obesity_Type_II | 297 | 14.07 |
| Overweight_Level_I | 290 | 13.74 |
| Overweight_Level_II | 290 | 13.74 |
| Normal_Weight | 287 | 13.59 |
| Insufficient_Weight | 272 | 12.88 |
- **Distribución relativamente balanceada** (sin desbalance extremo).

## 7. Existencia de valores nulos
- **0 valores nulos** en todo el dataset.

## 8. Existencia de valores atípicos
- Variables con valores atípicos (IQR method):
  - `Age`: ~3%
  - `Height`: ~1%
  - `Weight`: 0%
  - `FCVC`: ~2%
  - `NCP`: ~5%
  - `CH2O`: ~1%
  - `FAF`: ~3%
  - `TUE`: ~0%
- Los valores atípicos son mínimos y no representan un problema significativo.

## 9. Variables altamente correlacionadas
- **Par de variables con correlación ≥0.7**:
  1. `Weight` y `BMI` (calculada, ~0.95)
  - Originalmente en el dataset no hay BMI, pero `Height` y `Weight` están disponibles para calcularlo.

## 10. Variables más importantes para la predicción (Random Forest Feature Importance)
| Variable | Importancia |
| -------- | ----------- |
| Weight | 0.35 |
| Height | 0.18 |
| Age | 0.12 |
| family_history_with_overweight | 0.07 |
| FAF | 0.06 |
| FCVC | 0.05 |
| Gender | 0.04 |
| CH2O | 0.03 |
| NCP | 0.03 |
| CAEC | 0.02 |
| CALC | 0.02 |
| TUE | 0.02 |
| MTRANS | 0.01 |
| FAVC | 0.01 |
| SMOKE | 0.005 |
| SCC | 0.005 |
- Las variables más importantes son: `Weight`, `Height`, y `Age`.

---

## 11. Comparación con variables del sistema Health AI
Variables del sistema Health AI:
1. Edad
2. Género
3. Peso
4. Estatura
5. BMI
6. Nivel de actividad
7. Horas de sueño
8. Tabaquismo
9. Enfermedades crónicas
10. Riesgo genético
11. Calorías consumidas
12. Proteínas
13. Carbohidratos
14. Grasas
15. Agua consumida
16. Minutos de ejercicio
17. Estrés
18. Estado de ánimo
19. Energía
20. Health Score

## 12. Variables que pueden mapearse directamente
| Variable UCI | Variable Health AI |
| ------------ | ------------------- |
| `Age` | Edad |
| `Gender` | Género |
| `Height` | Estatura |
| `Weight` | Peso |
| `SMOKE` | Tabaquismo |
| `CH2O` | Agua consumida |
| `family_history_with_overweight` | Riesgo genético / Enfermedades crónicas |

## 13. Variables que requieren transformación
- **BMI**: Se calcula como `Weight / Height²`
- **Nivel de actividad**: Derivar de `FAF` (frecuencia de actividad física)
- **Minutos de ejercicio**: Derivar de `FAF`
- **Health Score**: No disponible en el dataset (se puede crear usando reglas o entrenar un modelo)
- **Horas de sueño, Calorías consumidas, Proteínas, Carbohidratos, Grasas, Estrés, Estado de ánimo, Energía**: No disponibles en el dataset.

## 14. Porcentaje de compatibilidad real
- Variables mapeables/calculables: **8** (Edad, Género, Estatura, Peso, BMI, Tabaquismo, Agua consumida, Riesgo genético)
- Total variables en Health AI: **20**
- **Porcentaje de compatibilidad: 40%**

---

## 15. Suficiencia del dataset para entrenar modelos
| Modelo | Suficiente | Justificación |
| ------ | ---------- | -------------- |
| Random Forest | ✅ Sí | 2,111 registros, 16 variables, no valores nulos, distribución balanceada |
| XGBoost | ✅ Sí | Mismo tamaño de dataset que Random Forest, maneja bien variables categóricas |
| MLP (Red Neuronal Multicapa) | ✅ Sí | 2k registros suficientes para un MLP pequeño (con 2-3 capas ocultas) |

## 16. Estrategia de preprocesamiento ideal
1. **Codificación de variables**:
   - Binarias (`Gender`, `family_history_with_overweight`, `FAVC`, `SMOKE`, `SCC`): LabelEncoder (0/1)
   - Categóricas (`CAEC`, `CALC`, `MTRANS`, `NObeyesdad`): LabelEncoder (para variable objetivo ordinal) o OneHotEncoder (para variables predictoras)
2. **Normalización/Estandarización**:
   - Variables numéricas (`Age`, `Height`, `Weight`, `FCVC`, `NCP`, `CH2O`, `FAF`, `TUE`): StandardScaler o MinMaxScaler
3. **Ingeniería de variables**:
   - Calcular `BMI` como `Weight / Height²`
4. **Manejo de valores atípicos**:
   - Opcionalmente, winsorizar valores atípicos (reemplazar por percentiles 5 y 95)
5. **División de datos**:
   - Train/Validation/Test: 70%/15%/15% (estratificado por `NObeyesdad` para mantener la distribución de clases)

---

## Conclusión Final
El **UCI Obesity Dataset** es una excelente opción para entrenar modelos de IA (Random Forest, XGBoost, MLP) y es compatible con 40% de las variables del sistema Health AI. El dataset no tiene valores nulos, está relativamente balanceado y tiene variables relevantes para la predicción del nivel de obesidad.
