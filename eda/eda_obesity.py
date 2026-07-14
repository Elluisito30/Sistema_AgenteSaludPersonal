
# -*- coding: utf-8 -*-
"""
EDA Script for UCI Obesity Dataset
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ucimlrepo import fetch_ucirepo
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# Set style for plots
sns.set(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

# Step 1: Fetch dataset
print("Fetching UCI Obesity Dataset...")
obesity_dataset = fetch_ucirepo(id=544)
X = obesity_dataset.data.features
y = obesity_dataset.data.targets
df = pd.concat([X, y], axis=1)
print("Dataset fetched successfully!")

# Step 2: Basic info
print("\n" + "="*50)
print("1. Number of records and variables")
print("="*50)
print(f"Total records: {df.shape[0]}")
print(f"Total variables: {df.shape[1]}")

print("\n" + "="*50)
print("2. Detailed description of each variable")
print("="*50)
print("\nFirst 5 rows:")
print(df.head())
print("\nData types and info:")
print(df.info())
print("\nSummary statistics:")
print(df.describe(include='all'))

print("\n" + "="*50)
print("3. Variable types")
print("="*50)
variable_types = []
for col in df.columns:
    unique_vals = df[col].nunique()
    dtype = df[col].dtype
    if dtype in ['int64', 'float64']:
        if unique_vals > 10:
            var_type = "Numérica continua"
        else:
            var_type = "Numérica discreta"
    else:
        if unique_vals == 2:
            var_type = "Binaria"
        else:
            var_type = "Categórica"
    variable_types.append({
        "Variable": col,
        "Tipo": var_type,
        "Valores únicos": unique_vals,
        "Ejemplos": list(df[col].unique()[:3])
    })
var_types_df = pd.DataFrame(variable_types)
print(var_types_df.to_string(index=False))

print("\n" + "="*50)
print("4. Variable objetivo")
print("="*50)
target_col = y.columns[0]
print(f"Variable objetivo: {target_col}")
print(f"Valores únicos: {df[target_col].unique()}")

print("\n" + "="*50)
print("5. Distribución de clases")
print("="*50)
class_dist = df[target_col].value_counts().sort_index()
class_dist_pct = df[target_col].value_counts(normalize=True).sort_index() * 100
print(pd.DataFrame({"Recuento": class_dist, "Porcentaje (%)": class_dist_pct}))

# Plot class distribution
plt.figure(figsize=(14, 6))
sns.countplot(data=df, x=target_col, order=df[target_col].unique())
plt.title("Distribución de la variable objetivo (Nivel de obesidad)")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("eda/class_distribution.png")
print("\nClass distribution plot saved to eda/class_distribution.png")

print("\n" + "="*50)
print("6. Valores nulos")
print("="*50)
missing = df.isnull().sum().sort_values(ascending=False)
missing_pct = (df.isnull().sum()/df.shape[0]) * 100
missing_df = pd.DataFrame({"Valores nulos": missing, "Porcentaje (%)": missing_pct})
print(missing_df)

print("\n" + "="*50)
print("7. Valores atípicos (IQR method)")
print("="*50)
numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
outlier_dict = {}
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5*IQR
    upper = Q3 + 1.5*IQR
    outliers = df[(df[col] < lower) | (df[col] > upper)].shape[0]
    outlier_dict[col] = outliers
    print(f"{col}: {outliers} valores atípicos ({(outliers/df.shape[0])*100:.2f}%)")

# Plot boxplots for numeric variables
plt.figure(figsize=(16, 10))
for i, col in enumerate(numeric_cols):
    plt.subplot(3, 3, i+1)
    sns.boxplot(y=df[col])
    plt.title(f"Boxplot - {col}")
plt.tight_layout()
plt.savefig("eda/boxplots_outliers.png")
print("\nBoxplots saved to eda/boxplots_outliers.png")

print("\n" + "="*50)
print("8. Correlación entre variables (numéricas)")
print("="*50)
corr_matrix = df[numeric_cols].corr()
print(corr_matrix)

# Plot heatmap
plt.figure(figsize=(14, 10))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
plt.title("Mapa de calor de correlaciones")
plt.tight_layout()
plt.savefig("eda/correlation_heatmap.png")
print("\nCorrelation heatmap saved to eda/correlation_heatmap.png")

# Find highly correlated variables
high_corr = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        if abs(corr_matrix.iloc[i,j]) >= 0.7:
            high_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i,j]))
print(f"\nPares de variables con correlación >= 0.7: {len(high_corr)}")
for pair in high_corr:
    print(f"- {pair[0]} y {pair[1]}: {pair[2]:.3f}")

print("\n" + "="*50)
print("9. Variables más importantes (Random Forest Feature Importance)")
print("="*50)
# Preprocess for Random Forest
df_encoded = df.copy()
label_encoders = {}
for col in df_encoded.columns:
    if df_encoded[col].dtype == 'object':
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df_encoded[col])
        label_encoders[col] = le

X_rf = df_encoded.drop(target_col, axis=1)
y_rf = df_encoded[target_col]
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_rf, y_rf)

feature_importance = pd.DataFrame({
    'Variable': X_rf.columns,
    'Importancia': rf.feature_importances_
}).sort_values(by='Importancia', ascending=False)
print(feature_importance.to_string(index=False))

# Plot feature importance
plt.figure(figsize=(14, 6))
sns.barplot(data=feature_importance, x='Importancia', y='Variable')
plt.title("Importancia de variables (Random Forest)")
plt.tight_layout()
plt.savefig("eda/feature_importance.png")
print("\nFeature importance plot saved to eda/feature_importance.png")

print("\n" + "="*50)
print("10. Comparación con variables del sistema Health AI")
print("="*50)

health_ai_vars = [
    "Edad", "Género", "Peso", "Estatura", "BMI", "Nivel de actividad", "Horas de sueño",
    "Tabaquismo", "Enfermedades crónicas", "Riesgo genético", "Calorías consumidas",
    "Proteínas", "Carbohidratos", "Grasas", "Agua consumida", "Minutos de ejercicio",
    "Estrés", "Estado de ánimo", "Energía", "Health Score"
]

uci_vars = df.columns.tolist()
mapping = {
    "Age": "Edad",
    "Gender": "Género",
    "Height": "Estatura",
    "Weight": "Peso",
    "SMOKE": "Tabaquismo",
    "CH2O": "Agua consumida",
    "FAF": "Minutos de ejercicio / Nivel de actividad",
    "family_history_with_overweight": "Riesgo genético / Enfermedades crónicas"
}
print("\nMapeo directo:")
for uci, health in mapping.items():
    if uci in uci_vars:
        print(f"  - {uci} (UCI) → {health} (Health AI)")
print("\nVariables que requieren transformación:")
print("  - BMI: Calcular desde Height y Weight (BMI = Weight / Height²)")
print("  - Nivel de actividad: Derivar de FAF")
print("  - Horas de sueño: No disponible en dataset")
print("  - Calorías consumidas, Proteínas, Carbohidratos, Grasas: No disponibles")
print("  - Estrés, Estado de ánimo, Energía, Health Score: No disponibles")

print("\n" + "="*50)
print("11. Porcentaje de compatibilidad real")
print("="*50)
mapped_count = len(mapping)
# Plus BMI (calculable)
mapped_count +=1
total_health_ai_vars = len(health_ai_vars)
compat_pct = (mapped_count / total_health_ai_vars)*100
print(f"Variables mapeables o calculables: {mapped_count} de {total_health_ai_vars}")
print(f"Porcentaje de compatibilidad: {compat_pct:.2f}%")

print("\n" + "="*50)
print("12. Viabilidad de modelos")
print("="*50)
print("- Random Forest: ✅ Suficiente (2111 registros, 16 variables)")
print("- XGBoost: ✅ Suficiente (mismo tamaño de dataset)")
print("- MLP: ✅ Suficiente (con preprocesamiento, 2k registros es suficiente para pequeño MLP)")

print("\n" + "="*50)
print("13. Estrategia de preprocesamiento recomendada")
print("="*50)
print("1. Codificar variables categóricas/binarias (LabelEncoder o OneHotEncoder)")
print("2. Normalizar/estandarizar variables numéricas (StandardScaler o MinMaxScaler)")
print("3. Calcular BMI desde Height y Weight")
print("4. Manejar valores atípicos (si es necesario: winsorizar o eliminar)")
print("5. Dividir dataset en train/validation/test (ej: 70/15/15)")

print("\n" + "="*50)
print("EDA COMPLETA")
print("="*50)

