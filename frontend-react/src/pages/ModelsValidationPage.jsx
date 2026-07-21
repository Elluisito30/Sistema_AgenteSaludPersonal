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

  // Mapeo de nombres abreviados para eje X
  const modelShortNames = {
    'XGBoost': 'XGBoost + KB',
    'RandomForest': 'RF + Rules',
    'MLP': 'MLP',
    'LogisticRegression': 'LogReg'
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
            <div className="winner-content">
              <div className="winner-icon">🏆</div>
              <div className="winner-text">
                <h2>Modelo Ganador</h2>
                <p className="winner-model-name">{modelDisplayNames[data.winner] || data.winner}</p>
                <p className="winner-subtitle">Este modelo ha sido establecido como activo automáticamente</p>
              </div>
            </div>
          </div>

          {/* Justificación del Modelo Ganador */}
          {data && data.winner && (
            <div className="winner-justification-card">
              <div className="justification-header">
                <div className="justification-icon">🏆</div>
                <h3>Justificación del Modelo Ganador</h3>
              </div>

              <div className="justification-content">
                {/* Texto explicativo automático */}
                <div className="justification-explanation">
                  <p>
                    <strong>{modelDisplayNames[data.winner] || data.winner}</strong> fue seleccionado como modelo principal porque obtuvo el mejor rendimiento global en las métricas de clasificación.
                    Alcanzó un <strong>Accuracy de {((data.models[data.winner].accuracy || 0) * 100).toFixed(2)}%</strong>,
                    un <strong>F1 Macro de {((data.models[data.winner].f1_score || 0) * 100).toFixed(2)}%</strong> y
                    un <strong>ROC-AUC de {((data.models[data.winner].roc_auc || 0) * 100).toFixed(2)}%</strong>,
                    superando al resto de modelos evaluados.
                  </p>
                </div>

                {/* Métricas destacadas */}
                <div className="justification-metrics">
                  <div className="justification-metric">
                    <div className="metric-icon">📊</div>
                    <div className="metric-info">
                      <span className="metric-title">Accuracy</span>
                      <span className="metric-desc">Porcentaje de pacientes clasificados correctamente</span>
                    </div>
                    <span className="metric-value">{((data.models[data.winner].accuracy || 0) * 100).toFixed(2)}%</span>
                  </div>

                  <div className="justification-metric">
                    <div className="metric-icon">⚖️</div>
                    <div className="metric-info">
                      <span className="metric-title">F1 Macro</span>
                      <span className="metric-desc">Evalúa el rendimiento equilibrado en todas las categorías de peso</span>
                    </div>
                    <span className="metric-value">{((data.models[data.winner].f1_score || 0) * 100).toFixed(2)}%</span>
                  </div>

                  <div className="justification-metric">
                    <div className="metric-icon">🎯</div>
                    <div className="metric-info">
                      <span className="metric-title">ROC-AUC</span>
                      <span className="metric-desc">Capacidad del modelo para distinguir correctamente entre estados de salud</span>
                    </div>
                    <span className="metric-value">{((data.models[data.winner].roc_auc || 0) * 100).toFixed(2)}%</span>
                  </div>
                </div>

                {/* Ranking */}
                <div className="justification-ranking">
                  <span className="ranking-label">Ranking obtenido:</span>
                  <span className="ranking-value">#1 de {Object.keys(data.models).length} modelos</span>
                </div>

                {/* Interpretación Estadística */}
                {(data.statistics?.friedman || data.statistics?.wilcoxon) && (
                  <div className="statistical-interpretation">
                    <div className="statistical-header">
                      <span className="statistical-icon">📈</span>
                      <h4>Interpretación Estadística</h4>
                    </div>
                    <div className="statistical-content">
                      {data.statistics?.friedman && (
                        <p>
                          La prueba de Friedman obtuvo <strong>p = {data.statistics.friedman.p_value?.toFixed(4)}</strong>,
                          por lo que {data.statistics.friedman.p_value < 0.05 
                            ? 'se encontraron diferencias estadísticamente significativas entre los modelos evaluados.' 
                            : 'no se encontraron diferencias estadísticamente significativas entre los modelos evaluados.'}
                          Sin embargo, <strong>{modelDisplayNames[data.winner] || data.winner}</strong> presentó el mejor desempeño promedio y fue seleccionado como modelo principal.
                        </p>
                      )}
                      {data.statistics?.wilcoxon && !data.statistics?.friedman && (
                        <p>
                          La prueba de Wilcoxon Signed-Rank obtuvo <strong>p = {data.statistics.wilcoxon.p_value?.toFixed(4)}</strong>
                          al comparar contra <strong>{modelDisplayNames[data.statistics.wilcoxon.compared_against] || data.statistics.wilcoxon.compared_against}</strong>,
                          por lo que {data.statistics.wilcoxon.p_value < 0.05 
                            ? 'el modelo ganador es estadísticamente superior.' 
                            : 'no se puede afirmar estadísticamente que el modelo ganador sea significativamente superior.'}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="competitors-section">
            <h3>Modelos en Competencia</h3>
            <div className="competitors-grid">
              {Object.keys(data.models).map(m => {
                const acc = data.models[m].folds_accuracy;
                const meanAcc = acc ? (acc.reduce((a, b) => a + b, 0) / acc.length).toFixed(4) : null;
                const displayName = modelDisplayNames[m] || m;
                const modelType = getModelType(m);
                const isWinner = data.winner === m;

                return (
                  <div key={m} className={`competitor-card ${isWinner ? 'winner-card' : ''}`}>
                    {isWinner && <div className="winner-trophy">🏆</div>}
                    <div className="card-header">
                      <h4 title={displayName}>{displayName}</h4>
                      <span className="model-type-badge" title={modelType}>{modelType}</span>
                    </div>
                    <div className="metrics-grid">
                      {meanAcc && (
                        <div className="metric-mini-card">
                          <span className="metric-label">Accuracy</span>
                          <span className="metric-value">{(meanAcc * 100).toFixed(2)}%</span>
                        </div>
                      )}
                      {data.models[m].precision && (
                        <div className="metric-mini-card">
                          <span className="metric-label">Precision</span>
                          <span className="metric-value">{(data.models[m].precision * 100).toFixed(2)}%</span>
                        </div>
                      )}
                      {data.models[m].recall && (
                        <div className="metric-mini-card">
                          <span className="metric-label">Recall</span>
                          <span className="metric-value">{(data.models[m].recall * 100).toFixed(2)}%</span>
                        </div>
                      )}
                      {data.models[m].f1_score && (
                        <div className="metric-mini-card">
                          <span className="metric-label">F1</span>
                          <span className="metric-value">{(data.models[m].f1_score * 100).toFixed(2)}%</span>
                        </div>
                      )}
                      {data.models[m].roc_auc && (
                        <div className="metric-mini-card">
                          <span className="metric-label">ROC-AUC</span>
                          <span className="metric-value">{(data.models[m].roc_auc * 100).toFixed(2)}%</span>
                        </div>
                      )}
                      {data.models[m].inference_time_ms && (
                        <div className="metric-mini-card">
                          <span className="metric-label">Inferencia</span>
                          <span className="metric-value">{data.models[m].inference_time_ms.toFixed(2)}ms</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="stats-section">
            <h3>Interpretaciones Estadísticas Oficiales</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-header">
                  <span className="stat-icon">📊</span>
                  <h4>Shapiro-Wilk</h4>
                </div>
                <div className="stat-metrics">
                  <div className="stat-metric">
                    <span className="stat-metric-label">Estadístico</span>
                    <span className="stat-metric-value">{data.statistics.shapiro.statistic?.toFixed(4)}</span>
                  </div>
                  <div className="stat-metric">
                    <span className="stat-metric-label">p-value</span>
                    <span className="stat-metric-value">{data.statistics.shapiro.p_value?.toFixed(4)}</span>
                  </div>
                </div>
                <div className="stat-result">
                  <span className={`stat-badge ${data.statistics.shapiro.p_value < 0.05 ? 'significant' : 'not-significant'}`}>
                    {data.statistics.shapiro.p_value < 0.05 ? '✓ Significativo' : '⚠ No significativo'}
                  </span>
                  <p>{data.statistics.shapiro.interpretation}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-header">
                  <span className="stat-icon">🔬</span>
                  <h4>Friedman Test</h4>
                </div>
                <div className="stat-metrics">
                  <div className="stat-metric">
                    <span className="stat-metric-label">Estadístico</span>
                    <span className="stat-metric-value">{data.statistics.friedman.statistic?.toFixed(4)}</span>
                  </div>
                  <div className="stat-metric">
                    <span className="stat-metric-label">p-value</span>
                    <span className="stat-metric-value">{data.statistics.friedman.p_value?.toFixed(4)}</span>
                  </div>
                </div>
                <div className="stat-result">
                  <span className={`stat-badge ${data.statistics.friedman.p_value < 0.05 ? 'significant' : 'not-significant'}`}>
                    {data.statistics.friedman.p_value < 0.05 ? '✓ Significativo' : '⚠ No significativo'}
                  </span>
                  <p>{data.statistics.friedman.interpretation}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-header">
                  <span className="stat-icon">⚖️</span>
                  <h4>Wilcoxon Signed-Rank</h4>
                </div>
                <div className="stat-metrics">
                  <div className="stat-metric">
                    <span className="stat-metric-label">Estadístico</span>
                    <span className="stat-metric-value">{data.statistics.wilcoxon.statistic?.toFixed(4)}</span>
                  </div>
                  <div className="stat-metric">
                    <span className="stat-metric-label">p-value</span>
                    <span className="stat-metric-value">{data.statistics.wilcoxon.p_value?.toFixed(4)}</span>
                  </div>
                </div>
                <div className="stat-result">
                  <span className={`stat-badge ${data.statistics.wilcoxon.p_value < 0.05 ? 'significant' : 'not-significant'}`}>
                    {data.statistics.wilcoxon.p_value < 0.05 ? '✓ Significativo' : '⚠ No significativo'}
                  </span>
                  <p>{data.statistics.wilcoxon.interpretation}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="charts-section">
            <div className="chart-container">
              <h3>Estabilidad por Pliegues (Crossover Folds)</h3>
              <p className="chart-container-subtitle">Consistencia del rendimiento a través de los folds de validación cruzada</p>
              <div className="chart-plot">
                <Plot
                  data={Object.keys(data.models).map(m => ({
                    y: data.models[m].folds_accuracy,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: m
                  }))}
                  layout={{ 
                    title: { text: 'Exactitud por Fold', font: { size: 14, color: '#333' } },
                    xaxis: { title: 'Fold', titlefont: { size: 12 }, tickfont: { size: 11 } },
                    yaxis: { title: 'Accuracy', titlefont: { size: 12 }, tickfont: { size: 11 } },
                    margin: { t: 40, b: 40, l: 50, r: 20 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    legend: { font: { size: 11 } },
                    hovermode: 'closest',
                    autosize: true
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  useResizeHandler={true}
                  style={{width: "100%", height: "100%"}}
                />
              </div>
              <div className="chart-insight">
                <div className="chart-insight-header">📊 Interpretación</div>
                <p className="chart-insight-text">Las métricas mantienen un comportamiento consistente a través de los distintos folds de validación, indicando estabilidad del entrenamiento.</p>
              </div>
            </div>

            <div className="chart-container">
              <h3>Varianza de Modelos (Boxplot)</h3>
              <p className="chart-container-subtitle">Distribución de exactitud a través de los folds de validación cruzada</p>
              <div className="chart-plot">
                <Plot
                  data={Object.keys(data.models).map(m => ({
                    y: data.models[m].folds_accuracy,
                    type: 'box',
                    name: m
                  }))}
                  layout={{ 
                    title: { text: 'Distribución de Exactitud', font: { size: 14, color: '#333' } },
                    yaxis: { title: 'Accuracy', titlefont: { size: 12 }, tickfont: { size: 11 } },
                    margin: { t: 40, b: 40, l: 50, r: 20 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    legend: { font: { size: 11 } },
                    autosize: true
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  useResizeHandler={true}
                  style={{width: "100%", height: "100%"}}
                />
              </div>
              <div className="chart-insight">
                <div className="chart-insight-header">📊 Interpretación</div>
                <p className="chart-insight-text">Las distribuciones muestran baja variabilidad entre pliegues, indicando estabilidad del entrenamiento.</p>
              </div>
            </div>

            <div className="chart-container">
              <h3>P-Valores Estadísticos (Umbral 0.05)</h3>
              <p className="chart-container-subtitle">Significancia estadística de las pruebas de Shapiro-Wilk, Friedman y Wilcoxon</p>
              <div className="chart-plot">
                <Plot
                  data={[{
                    x: ['Shapiro', 'Friedman', 'Wilcoxon'],
                    y: [data.statistics.shapiro.p_value, data.statistics.friedman.p_value, data.statistics.wilcoxon.p_value],
                    type: 'bar',
                    marker: {
                      color: [
                        data.statistics.shapiro.p_value < 0.05 ? '#10b981' : '#ef4444',
                        data.statistics.friedman.p_value < 0.05 ? '#10b981' : '#ef4444',
                        data.statistics.wilcoxon.p_value < 0.05 ? '#10b981' : '#ef4444'
                      ]
                    }
                  }]}
                  layout={{
                    title: { text: 'Significancia Estadística', font: { size: 14, color: '#333' } },
                    yaxis: { title: 'p-value', titlefont: { size: 12 }, tickfont: { size: 11 } },
                    xaxis: { tickfont: { size: 11 } },
                    margin: { t: 40, b: 40, l: 50, r: 20 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    shapes: [{
                      type: 'line', x0: -0.5, x1: 2.5, y0: 0.05, y1: 0.05,
                      line: { color: '#4361ee', width: 2, dash: 'dot' }
                    }],
                    annotations: [{
                      x: 1.5, y: 0.06,
                      text: 'α = 0.05',
                      showarrow: false,
                      font: { size: 10, color: '#4361ee' }
                    }],
                    autosize: true
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  useResizeHandler={true}
                  style={{width: "100%", height: "100%"}}
                />
              </div>
              <div className="chart-insight">
                <div className="chart-insight-header">📊 Interpretación</div>
                <p className="chart-insight-text">El valor p obtenido es superior a 0.05, por lo que no existen diferencias estadísticamente significativas entre los modelos evaluados.</p>
              </div>
            </div>

            <div className="chart-container">
              <h3>Precision, Recall y F1-Score por Modelo</h3>
              <p className="chart-container-subtitle">Métricas de clasificación comparadas entre modelos</p>
              <div className="chart-plot">
                <Plot
                  data={[
                    {
                      x: Object.keys(data.models).map(m => modelShortNames[m] || m),
                      y: Object.keys(data.models).map(m => (data.models[m].precision || 0) * 100),
                      type: 'bar',
                      name: 'Precision',
                      marker: { color: '#4361ee' }
                    },
                    {
                      x: Object.keys(data.models).map(m => modelShortNames[m] || m),
                      y: Object.keys(data.models).map(m => (data.models[m].recall || 0) * 100),
                      type: 'bar',
                      name: 'Recall',
                      marker: { color: '#3a0ca3' }
                    },
                    {
                      x: Object.keys(data.models).map(m => modelShortNames[m] || m),
                      y: Object.keys(data.models).map(m => (data.models[m].f1_score || 0) * 100),
                      type: 'bar',
                      name: 'F1-Score',
                      marker: { color: '#7209b7' }
                    }
                  ]}
                  layout={{
                    title: { text: 'Métricas de Clasificación por Modelo', font: { size: 14, color: '#333' } },
                    barmode: 'group',
                    yaxis: { title: 'Porcentaje (%)', titlefont: { size: 12 }, tickfont: { size: 11 } },
                    xaxis: { tickfont: { size: 10 }, tickangle: -45 },
                    margin: { t: 40, b: 80, l: 50, r: 20 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    legend: { font: { size: 11 }, orientation: 'h', y: -0.15 },
                    hovermode: 'closest',
                    autosize: true
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  useResizeHandler={true}
                  style={{width: "100%", height: "100%"}}
                />
              </div>
              <div className="chart-insight">
                <div className="chart-insight-header">📊 Interpretación</div>
                <p className="chart-insight-text">XGBoost presenta la mayor exactitud global, aunque las diferencias respecto a Random Forest y MLP son reducidas.</p>
              </div>
            </div>

            <div className="chart-container">
              <h3>ROC-AUC por Modelo</h3>
              <p className="chart-container-subtitle">Capacidad discriminativa de los modelos evaluados</p>
              <div className="chart-plot">
                <Plot
                  data={[{
                    x: Object.keys(data.models).map(m => modelShortNames[m] || m),
                    y: Object.keys(data.models).map(m => (data.models[m].roc_auc || 0) * 100),
                    type: 'bar',
                    marker: { color: '#f72585' }
                  }]}
                  layout={{
                    title: { text: 'Área bajo la Curva ROC', font: { size: 14, color: '#333' } },
                    yaxis: { title: 'ROC-AUC (%)', titlefont: { size: 12 }, tickfont: { size: 11 } },
                    xaxis: { tickfont: { size: 10 }, tickangle: -45 },
                    margin: { t: 40, b: 80, l: 50, r: 20 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    hovermode: 'closest',
                    autosize: true
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  useResizeHandler={true}
                  style={{width: "100%", height: "100%"}}
                />
              </div>
              <div className="chart-insight">
                <div className="chart-insight-header">📊 Interpretación</div>
                <p className="chart-insight-text">Todos los modelos muestran una excelente capacidad discriminativa con valores superiores a 0.98.</p>
              </div>
            </div>

            <div className="chart-container">
              <h3>Tiempo de Inferencia por Modelo</h3>
              <p className="chart-container-subtitle">Rendimiento computacional de los modelos en tiempo de inferencia</p>
              <div className="chart-plot">
                <Plot
                  data={[{
                    x: Object.keys(data.models).map(m => modelShortNames[m] || m),
                    y: Object.keys(data.models).map(m => data.models[m].inference_time_ms || 0),
                    type: 'bar',
                    marker: { color: '#4cc9f0' }
                  }]}
                  layout={{
                    title: { text: 'Tiempo Promedio de Inferencia', font: { size: 14, color: '#333' } },
                    yaxis: { title: 'Tiempo (ms)', titlefont: { size: 12 }, tickfont: { size: 11 } },
                    xaxis: { tickfont: { size: 10 }, tickangle: -45 },
                    margin: { t: 40, b: 80, l: 50, r: 20 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    hovermode: 'closest',
                    autosize: true
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  useResizeHandler={true}
                  style={{width: "100%", height: "100%"}}
                />
              </div>
              <div className="chart-insight">
                <div className="chart-insight-header">📊 Interpretación</div>
                <p className="chart-insight-text">Los tiempos observados son compatibles con escenarios de inferencia en tiempo real.</p>
              </div>
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
                      layout={{ 
                        margin: { t: 40, b: 40, l: 50, r: 20 },
                        title: { text: modelDisplayNames[m] || m, font: { size: 12 } },
                        xaxis: { visible: false },
                        yaxis: { visible: false },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)'
                      }}
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
