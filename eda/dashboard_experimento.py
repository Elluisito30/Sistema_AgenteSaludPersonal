
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

# Configurar página
st.set_page_config(page_title="Dashboard de Experimento: Predicción de Obesidad", layout="wide", page_icon="📊")

# Rutas de archivos
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"

# Título principal
st.title("📊 Dashboard Científico: Predicción de Niveles de Obesidad")
st.markdown("---")

# Función para cargar datos
@st.cache_data
def cargar_datos():
    try:
        holdout_results = pd.read_csv(MODELS_DIR / "holdout_test_results.csv")
        cv_results = pd.read_csv(MODELS_DIR / "cv_results.csv")
        statistical_results = pd.read_csv(MODELS_DIR / "statistical_results.csv")
        nemenyi_results = None
        if (MODELS_DIR / "nemenyi_results.csv").exists():
            nemenyi_results = pd.read_csv(MODELS_DIR / "nemenyi_results.csv", index_col=0)
        return holdout_results, cv_results, statistical_results, nemenyi_results
    except FileNotFoundError as e:
        st.error(f"Archivo no encontrado: {e.filename}")
        st.stop()

# Cargar datos
holdout_results, cv_results, statistical_results, nemenyi_results = cargar_datos()

# ==================== SECCIÓN 1: TARJETAS KPI ====================
st.header("📈 Principales Resultados (Hold-Out Test)")
col1, col2, col3, col4 = st.columns(4)

# Encontrar mejor modelo para cada métrica
holdout_results.set_index("model", inplace=True)

# Mejor Accuracy
best_acc_model = holdout_results["accuracy"].idxmax()
best_acc_value = holdout_results.loc[best_acc_model, "accuracy"]

# Mejor F1 Macro
best_f1_model = holdout_results["f1_macro"].idxmax()
best_f1_value = holdout_results.loc[best_f1_model, "f1_macro"]

# Mejor ROC AUC
best_roc_model = holdout_results["roc_auc_ovr"].idxmax()
best_roc_value = holdout_results.loc[best_roc_model, "roc_auc_ovr"]

# Modelo ganador general (promedio de métricas normalizadas)
metricas = ["accuracy", "balanced_accuracy", "cohen_kappa", "f1_macro", "f1_weighted", "roc_auc_ovr"]
normalized = holdout_results[metricas].apply(lambda x: (x - x.min()) / (x.max() - x.min()))
holdout_results["promedio_normalizado"] = normalized.mean(axis=1)
best_overall_model = holdout_results["promedio_normalizado"].idxmax()

with col1:
    st.metric(label="Mejor Accuracy", value=f"{best_acc_value:.4f}", delta=f"{best_acc_model}")
with col2:
    st.metric(label="Mejor F1 Macro", value=f"{best_f1_value:.4f}", delta=f"{best_f1_model}")
with col3:
    st.metric(label="Mejor ROC-AUC OvR", value=f"{best_roc_value:.4f}", delta=f"{best_roc_model}")
with col4:
    st.metric(label="Modelo Ganador General", value=best_overall_model)

st.markdown("---")

# ==================== SECCIÓN 2: TABLA COMPARATIVA ====================
st.header("📋 Tabla Comparativa de Modelos")
st.dataframe(
    holdout_results.round(4),
    use_container_width=True,
    column_config={
        "accuracy": st.column_config.NumberColumn("Accuracy", format="%.4f"),
        "balanced_accuracy": st.column_config.NumberColumn("Balanced Accuracy", format="%.4f"),
        "cohen_kappa": st.column_config.NumberColumn("Cohen's Kappa", format="%.4f"),
        "f1_macro": st.column_config.NumberColumn("F1 Macro", format="%.4f"),
        "f1_weighted": st.column_config.NumberColumn("F1 Weighted", format="%.4f"),
        "roc_auc_ovr": st.column_config.NumberColumn("ROC AUC OvR", format="%.4f"),
        "promedio_normalizado": st.column_config.NumberColumn("Promedio Normalizado", format="%.4f"),
    },
)

# ==================== SECCIÓN 3: GRÁFICOS DE BARRAS ====================
st.header("📊 Gráficos de Comparación de Métricas")

# Preparar datos para gráficos
holdout_reset = holdout_results.reset_index()
metricas_barras = ["accuracy", "balanced_accuracy", "f1_macro", "cohen_kappa", "roc_auc_ovr"]

# Crear gráfico de barras combinado
fig_barras = go.Figure()
colors = px.colors.qualitative.D3

for idx, metrica in enumerate(metricas_barras):
    fig_barras.add_trace(
        go.Bar(
            x=holdout_reset["model"],
            y=holdout_reset[metrica],
            name=metrica.replace("_", " ").title(),
            marker_color=colors[idx % len(colors)],
        )
    )

fig_barras.update_layout(
    title="Comparación de Métricas entre Modelos",
    barmode="group",
    xaxis_title="Modelo",
    yaxis_title="Valor",
    height=600,
    legend_title="Métrica",
    template="plotly_white",
)

st.plotly_chart(fig_barras, use_container_width=True)
st.caption("**Interpretación**: Este gráfico muestra el rendimiento de cada modelo en todas las métricas de forma agrupada, facilitando la comparación visual.")

# ==================== SECCIÓN 4: RADAR CHART ====================
st.header("🔄 Radar Chart: Rendimiento Multidimensional")

# Preparar datos para radar chart
metricas_radar = ["accuracy", "balanced_accuracy", "cohen_kappa", "f1_macro", "roc_auc_ovr"]
radar_data = holdout_reset.melt(
    id_vars="model",
    value_vars=metricas_radar,
    var_name="metrica",
    value_name="valor"
)
radar_data["metrica"] = radar_data["metrica"].replace({
    "accuracy": "Accuracy",
    "balanced_accuracy": "Balanced Acc.",
    "cohen_kappa": "Cohen Kappa",
    "f1_macro": "F1 Macro",
    "roc_auc_ovr": "ROC AUC"
})

fig_radar = go.Figure()

for model in holdout_reset["model"]:
    model_data = radar_data[radar_data["model"] == model]
    fig_radar.add_trace(
        go.Scatterpolar(
            r=model_data["valor"],
            theta=model_data["metrica"],
            fill='toself',
            name=model
        )
    )

fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 1]),
    ),
    showlegend=True,
    title="Radar Chart de Rendimiento por Modelo",
    height=600,
    template="plotly_white",
)

st.plotly_chart(fig_radar, use_container_width=True)
st.caption("**Interpretación**: El radar chart compara el rendimiento multidimensional de los modelos. Un área más grande y cercana a 1 indica un mejor rendimiento general.")

# ==================== SECCIÓN 5: HEATMAP DE MÉTRICAS ====================
st.header("🔥 Heatmap de Correlación y Comparación")

# Heatmap de valores de métricas
heatmap_data = holdout_results[metricas_radar].T
heatmap_data.columns.name = "Modelo"
heatmap_data.index.name = "Métrica"

fig_heatmap = px.imshow(
    heatmap_data,
    text_auto=".4f",
    color_continuous_scale="Blues",
    aspect="auto",
    title="Heatmap de Rendimiento por Modelo y Métrica"
)

fig_heatmap.update_layout(height=500)

st.plotly_chart(fig_heatmap, use_container_width=True)
st.caption("**Interpretación**: El heatmap visualiza el valor de cada métrica para cada modelo. Tonos más oscuros indican mejor rendimiento.")

# ==================== SECCIÓN 6: MATRIZ DE CONFUSIÓN ====================
st.header("🔍 Matriz de Confusión (MLP - Hold-Out Test)")
confusion_path = MODELS_DIR / "confusion_matrix_mlp_test.png"
if confusion_path.exists():
    st.image(str(confusion_path), caption="Matriz de Confusión del MLP", use_container_width=True)
else:
    st.warning("Imagen de matriz de confusión no encontrada.")
st.caption("**Interpretación**: La matriz de confusión muestra los verdaderos positivos, falsos positivos, verdaderos negativos y falsos negativos para cada clase, permitiendo identificar patrones de error específicos.")

st.markdown("---")

# ==================== SECCIÓN 7: CURVA DE ENTRENAMIENTO MLP ====================
st.header("📉 Curva de Entrenamiento (MLP)")
training_history_path = MODELS_DIR / "mlp_final_training_history.png"
if training_history_path.exists():
    st.image(str(training_history_path), caption="Curvas de Loss y Accuracy durante el entrenamiento del MLP", use_container_width=True)
else:
    st.warning("Imagen de curva de entrenamiento no encontrada.")
st.caption("**Interpretación**: Las curvas de entrenamiento muestran la evolución de la pérdida (loss) y la precisión (accuracy) en los conjuntos de entrenamiento y validación. Un gap pequeño indica un buen ajuste.")

st.markdown("---")

# ==================== SECCIÓN 8: PRUEBAS ESTADÍSTICAS ====================
st.header("📊 Pruebas Estadísticas")

# Prueba de Friedman
st.subheader("Prueba de Friedman")
st.dataframe(statistical_results.round(4), use_container_width=True)
friedman_p = statistical_results.loc[0, "p_value"]
if friedman_p < 0.05:
    st.success(f"✅ La prueba de Friedman es significativa (p-value = {friedman_p:.4f} < 0.05). Hay diferencias estadísticamente significativas entre los modelos.")
else:
    st.info(f"ℹ️ La prueba de Friedman NO es significativa (p-value = {friedman_p:.4f} ≥ 0.05). No hay diferencias estadísticamente significativas entre los modelos con un nivel de confianza del 95%.")

# Prueba de Nemenyi (si existe)
if nemenyi_results is not None:
    st.subheader("Prueba Post-Hoc de Nemenyi")
    st.dataframe(
        nemenyi_results.round(4),
        use_container_width=True,
        column_config={col: st.column_config.NumberColumn(col, format="%.4f") for col in nemenyi_results.columns}
    )
    st.caption("**Interpretación**: La matriz de Nemenyi muestra los valores p ajustados entre cada par de modelos. Valores < 0.05 indican diferencias significativas.")
else:
    st.info("ℹ️ No se encontraron resultados de la prueba de Nemenyi (no era necesaria porque la prueba de Friedman no fue significativa).")

# ==================== SECCIÓN 9: RESULTADOS DE VALIDACIÓN CRUZADA ====================
st.markdown("---")
st.header("📁 Resultados Completos de Validación Cruzada")
with st.expander("Ver resultados de CV (todos los folds)"):
    st.dataframe(cv_results.round(4), use_container_width=True)

