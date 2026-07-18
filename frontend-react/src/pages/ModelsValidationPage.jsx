import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { FrontendModel } from '../ml/frontend_model';
import './ModelsValidationPage.css';

export default function ModelsValidationPage() {
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [currentModel, setCurrentModel] = useState(null);

  const fetchCurrentModel = async () => {
    const res = await apiRequest('/api/models/current', 'GET', null, token);
    if (res.success) {
      setCurrentModel(res.data.active_model);
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

      // 2. Run local frontend model
      const jsModel = new FrontendModel();
      const y_pred = jsModel.evaluate(X);

      // 3. Send predictions to backend for full evaluation
      const evalRes = await apiRequest('/api/models/evaluate-all', 'POST', { y_pred }, token);
      
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
      
      {error && <div className="validation-error">{error}</div>}

      {currentModel && !loading && !data && (
        <div className="current-model-info">
          Modelo Activo Actual: <strong>{currentModel}</strong>
          <p>Presiona "Ejecutar Evaluación Completa" para comparar todos los modelos estadísticamente.</p>
        </div>
      )}

      {data && (
        <div className="validation-results">
          <div className="winner-banner">
            <h2>🏆 Modelo Ganador: {data.winner}</h2>
            <p>Este modelo ha sido establecido como activo automáticamente.</p>
          </div>

          <div className="competitors-section">
            <h3>Modelos en Competencia</h3>
            <div className="competitors-grid">
              {Object.keys(data.models).map(m => {
                const acc = data.models[m].folds_accuracy;
                const meanAcc = acc ? (acc.reduce((a, b) => a + b, 0) / acc.length).toFixed(4) : null;
                
                let modelType = "ML Clásico";
                const lowerM = m.toLowerCase();
                if (lowerM.includes("mlp") || lowerM.includes("red neuronal")) modelType = "Red Neuronal";
                else if (lowerM.includes("local") || lowerM.includes("js") || lowerM.includes("frontend")) modelType = "Modelo Híbrido (Local)";

                return (
                  <div key={m} className={`competitor-card ${data.winner === m ? 'winner-card' : ''}`}>
                    <h4>{m}</h4>
                    {meanAcc && <p>Precisión: {(meanAcc * 100).toFixed(2)}%</p>}
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
                <h4>Superioridad por Pares (McNemar Test)</h4>
                <p>{data.statistics.mcnemar.interpretation}</p>
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
                  x: ['Shapiro', 'Friedman', 'McNemar'],
                  y: [data.statistics.shapiro.p_value, data.statistics.friedman.p_value, data.statistics.mcnemar.p_value],
                  type: 'bar',
                  marker: {
                    color: [
                      data.statistics.shapiro.p_value < 0.05 ? 'green' : 'red',
                      data.statistics.friedman.p_value < 0.05 ? 'green' : 'red',
                      data.statistics.mcnemar.p_value < 0.05 ? 'green' : 'red'
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
            
            <div className="matrices-section">
              <h3>Matrices de Confusión</h3>
              <div className="matrices-grid">
                {Object.keys(data.models).map(m => (
                  <div key={m} className="matrix-plot">
                    <h4>{m}</h4>
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
