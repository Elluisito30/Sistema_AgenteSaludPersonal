import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import './ModelsValidationPage.css';

export default function ModelsValidationPage() {
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);
  const [modelType, setModelType] = useState(null);

  // Mapeo de nombres de modelos para presentación
  const modelDisplayNames = {
    'XGBoost': 'XGBoost + Motor Basado en Conocimiento',
    'RandomForest': 'Random Forest + Sistema Basado en Reglas Médicas',
    'MLP': 'MLP (Deep Learning)',
    'LogisticRegression': 'Regresión Logística'
  };

  const getModelType = (modelName) => {
    const lowerM = modelName.toLowerCase();
    if (lowerM.includes("xgboost")) return "Híbrido: XGBoost + Motor Basado en Conocimiento";
    if (lowerM.includes("randomforest")) return "Híbrido: Random Forest + Reglas Médicas";
    if (lowerM.includes("mlp")) return "Clásico: MLP (Deep Learning)";
    if (lowerM.includes("logistic") || lowerM.includes("regression")) return "Clásico: Regresión Logística";
    return "ML Clásico";
  };

  const fetchCurrentModel = async () => {
    const res = await apiRequest('/api/models/current', 'GET', null, token);
    if (res.success) {
      setCurrentModel(res.data.active_model);
    }
  };

  const fetchModelType = async () => {
    const res = await apiRequest('/api/training/model-type', 'GET', null, token);
    if (res.success) {
      setModelType(res.data);
    }
  };

  const runEvaluation = async () => {
    try {
      setLoading(true);
      setError(null);
      setData(null);

      // 1. Get test dataset from backend
      const testRes = await apiRequest('/api/models/test-data', 'GET', null, token);
      if (!testRes.success) throw new Error("Error obteniendo datos de prueba");
      
      const { X, y, classes } = testRes.data;

      // 2. Send empty predictions to backend (evaluate only backend models)
      const evalRes = await apiRequest('/api/models/evaluate-all', 'POST', { y_pred: [] }, token);
      
      if (!evalRes.success) throw new Error("Error en la evaluación estadística");

      setData(evalRes.data);
      await fetchCurrentModel();
    } catch (err) {
      setError(err.message || 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentModel();
    fetchModelType();
  }, [token]);

  if (loading) {
    return (
      <div className="validation-loading">
        <div className="spinner"></div>
        <h2>Ejecutando Validación Estadística...</h2>
        <p>Cargando XGBoost, Random Forest, MLP y evaluando TensorFlow.js local</p>
      </div>
    );
  }

  return (
    <div className="models-validation-container">
      <header className="validation-header">
        <h1>🧠 Panel de Validación de Modelos</h1>
        <button className="btn-run" onClick={runEvaluation}>Ejecutar Evaluación Completa</button>
      </header>
      
      {modelType && (
        <div style={{
          padding: '10px 15px',
          margin: '10px 0',
          borderRadius: '4px',
          background: modelType.model_type === 'custom' ? '#d4edda' : '#e2e3e5',
          color: modelType.model_type === 'custom' ? '#155724' : '#383d41',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '1.2rem' }}>{modelType.model_type === 'custom' ? '✅' : 'ℹ️'}</span>
          <span>{modelType.message}</span>
        </div>
      )}

      {!data && (
        <div className="stat-card" style={{ 
          padding: '20px', 
          background: '#fff3e0', 
          borderLeft: '4px solid #ff9800',
          marginBottom: '20px'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#f57c00' }}>👋 Bienvenido a la Validación de Modelos</h4>
          <p style={{ margin: '0', color: '#424242' }}>
            Esta sección te permite comparar el rendimiento de los modelos de Machine Learning (XGBoost, RandomForest, MLP).
            <br /><br />
            <strong>💡 Tip:</strong> Presiona el botón "Ejecutar Evaluación Completa" para comparar los modelos mediante pruebas estadísticas.
            El sistema seleccionará automáticamente el mejor modelo basado en los resultados.
          </p>
        </div>
      )}
      
      {error && <div className="validation-error">{error}</div>}


      {data && (
        <div className="validation-results">
          <div className="winner-banner">
            <h2>🏆 Modelo Ganador: {modelDisplayNames[data.winner] || data.winner}</h2>
            <p>Este modelo ha sido establecido como activo automáticamente.</p>
          </div>

          <div className="competitors-section">
            <h3>Modelos en Competencia</h3>
            <div className="competitors-grid">
              {Object.keys(data.models).map(m => {
                const acc = data.models[m].folds_accuracy;
                const meanAcc = acc ? (acc.reduce((a, b) => a + b, 0) / acc.length).toFixed(4) : null;
                const displayName = modelDisplayNames[m] || m;
                const modelType = getModelType(m);

                return (
                  <div key={m} className={`competitor-card ${data.winner === m ? 'winner-card' : ''}`}>
                    <h4>{displayName}</h4>
                    {meanAcc && <p>Accuracy: {(meanAcc * 100).toFixed(2)}%</p>}
                    {data.models[m].precision && <p>Precision: {(data.models[m].precision * 100).toFixed(2)}%</p>}
                    {data.models[m].recall && <p>Recall: {(data.models[m].recall * 100).toFixed(2)}%</p>}
                    {data.models[m].f1_score && <p>F1-Score: {(data.models[m].f1_score * 100).toFixed(2)}%</p>}
                    {data.models[m].roc_auc && <p>ROC-AUC: {(data.models[m].roc_auc * 100).toFixed(2)}%</p>}
                    {data.models[m].inference_time_ms && <p>Inferencia: {data.models[m].inference_time_ms.toFixed(2)}ms</p>}
                    <p style={{ fontSize: '0.85rem', marginTop: '4px', fontWeight: 600, color: 'var(--primary-color, #4361ee)' }}>
                      Tipo: {modelType}
                    </p>
                    {data.winner === m && <span className="winner-badge">Ganador</span>}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="stats-section">
            <h3>Interpretaciones Estadísticas Oficiales</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <h4>Prueba de Normalidad (Shapiro-Wilk)</h4>
                <p>{data.statistics.shapiro.interpretation}</p>
              </div>
              <div className="stat-card">
                <h4>Comparación Global (Friedman Test)</h4>
                <p>{data.statistics.friedman.interpretation}</p>
              </div>
              <div className="stat-card">
                <h4>Superioridad por Pares (Wilcoxon Signed-Rank)</h4>
                <p>{data.statistics.wilcoxon.interpretation}</p>
              </div>
            </div>
          </div>

          <div className="charts-section">
            <div className="chart-container">
              <h3>Estabilidad por Pliegues (Crossover Folds)</h3>
              <Plot
                data={Object.keys(data.models).map(m => ({
                  y: data.models[m].folds_accuracy,
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: m
                }))}
                layout={{ title: 'Exactitud por Fold', xaxis: {title: 'Fold'}, yaxis: {title: 'Accuracy'} }}
                useResizeHandler={true}
                style={{width: "100%", height: "100%"}}
              />
            </div>

            <div className="chart-container">
              <h3>Varianza de Modelos (Boxplot)</h3>
              <Plot
                data={Object.keys(data.models).map(m => ({
                  y: data.models[m].folds_accuracy,
                  type: 'box',
                  name: m
                }))}
                layout={{ title: 'Distribución de Exactitud' }}
                useResizeHandler={true}
                style={{width: "100%", height: "100%"}}
              />
            </div>

            <div className="chart-container">
              <h3>P-Valores Estadísticos (Umbral 0.05)</h3>
              <Plot
                data={[{
                  x: ['Shapiro', 'Friedman', 'Wilcoxon'],
                  y: [data.statistics.shapiro.p_value, data.statistics.friedman.p_value, data.statistics.wilcoxon.p_value],
                  type: 'bar',
                  marker: {
                    color: [
                      data.statistics.shapiro.p_value < 0.05 ? 'green' : 'red',
                      data.statistics.friedman.p_value < 0.05 ? 'green' : 'red',
                      data.statistics.wilcoxon.p_value < 0.05 ? 'green' : 'red'
                    ]
                  }
                }]}
                layout={{
                  title: 'Significancia Estadística',
                  shapes: [{
                    type: 'line', x0: -0.5, x1: 2.5, y0: 0.05, y1: 0.05,
                    line: { color: 'blue', width: 2, dash: 'dot' }
                  }]
                }}
                useResizeHandler={true}
                style={{width: "100%", height: "100%"}}
              />
            </div>

            <div className="chart-container">
              <h3>Precision, Recall y F1-Score por Modelo</h3>
              <Plot
                data={[
                  {
                    x: Object.keys(data.models).map(m => modelDisplayNames[m] || m),
                    y: Object.keys(data.models).map(m => (data.models[m].precision || 0) * 100),
                    type: 'bar',
                    name: 'Precision',
                    marker: { color: '#4361ee' }
                  },
                  {
                    x: Object.keys(data.models).map(m => modelDisplayNames[m] || m),
                    y: Object.keys(data.models).map(m => (data.models[m].recall || 0) * 100),
                    type: 'bar',
                    name: 'Recall',
                    marker: { color: '#3a0ca3' }
                  },
                  {
                    x: Object.keys(data.models).map(m => modelDisplayNames[m] || m),
                    y: Object.keys(data.models).map(m => (data.models[m].f1_score || 0) * 100),
                    type: 'bar',
                    name: 'F1-Score',
                    marker: { color: '#7209b7' }
                  }
                ]}
                layout={{
                  title: 'Métricas de Clasificación por Modelo',
                  barmode: 'group',
                  yaxis: { title: 'Porcentaje (%)' }
                }}
                useResizeHandler={true}
                style={{width: "100%", height: "100%"}}
              />
            </div>

            <div className="chart-container">
              <h3>ROC-AUC por Modelo</h3>
              <Plot
                data={[{
                  x: Object.keys(data.models).map(m => modelDisplayNames[m] || m),
                  y: Object.keys(data.models).map(m => (data.models[m].roc_auc || 0) * 100),
                  type: 'bar',
                  marker: { color: '#f72585' }
                }]}
                layout={{
                  title: 'Área bajo la Curva ROC',
                  yaxis: { title: 'ROC-AUC (%)' }
                }}
                useResizeHandler={true}
                style={{width: "100%", height: "100%"}}
              />
            </div>

            <div className="chart-container">
              <h3>Tiempo de Inferencia por Modelo</h3>
              <Plot
                data={[{
                  x: Object.keys(data.models).map(m => modelDisplayNames[m] || m),
                  y: Object.keys(data.models).map(m => data.models[m].inference_time_ms || 0),
                  type: 'bar',
                  marker: { color: '#4cc9f0' }
                }]}
                layout={{
                  title: 'Tiempo Promedio de Inferencia',
                  yaxis: { title: 'Tiempo (ms)' }
                }}
                useResizeHandler={true}
                style={{width: "100%", height: "100%"}}
              />
            </div>
            
            <div className="matrices-section">
              <h3>Matrices de Confusión</h3>
              <div className="matrices-grid">
                {Object.keys(data.models).map(m => (
                  <div key={m} className="matrix-plot">
                    <h4>{modelDisplayNames[m] || m}</h4>
                    <Plot
                      data={[{
                        z: data.models[m].confusion_matrix,
                        type: 'heatmap',
                        colorscale: 'Blues'
                      }]}
                      layout={{ margin: { t: 10, b: 30, l: 30, r: 10 } }}
                      useResizeHandler={true}
                      style={{width: "100%", height: "250px"}}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
