import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import './ModelsValidationPage.css';

export default function ModelTrainingPage() {
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [hyperparameters, setHyperparameters] = useState(null);
  const [history, setHistory] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [error, setError] = useState(null);

  const loadTrainingData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [datasetRes, hyperRes, historyRes, modelRes] = await Promise.all([
        apiRequest('/api/training/dataset-info', 'GET', null, token),
        apiRequest('/api/training/hyperparameters', 'GET', null, token),
        apiRequest('/api/training/history', 'GET', null, token),
        apiRequest('/api/training/model-status', 'GET', null, token)
      ]);

      if (datasetRes.success) setDatasetInfo(datasetRes.data);
      if (hyperRes.success) setHyperparameters(hyperRes.data);
      if (historyRes.success) setHistory(historyRes.data);
      if (modelRes.success) setModelStatus(modelRes.data);
    } catch (err) {
      setError(err.message || 'Error al cargar datos de entrenamiento');
    } finally {
      setLoading(false);
    }
  };

  const runTraining = async () => {
    try {
      setTraining(true);
      setError(null);
      
      const res = await apiRequest('/api/training/run-all', 'POST', null, token);
      
      if (res.success) {
        await loadTrainingData();
      } else {
        setError(res.error || 'Error durante el entrenamiento');
      }
    } catch (err) {
      setError(err.message || 'Error al ejecutar entrenamiento');
    } finally {
      setTraining(false);
    }
  };

  useEffect(() => {
    loadTrainingData();
  }, [token]);

  if (loading) {
    return (
      <div className="validation-loading">
        <div className="spinner"></div>
        <h2>Cargando información de entrenamiento...</h2>
      </div>
    );
  }

  return (
    <div className="models-validation-container">
      <header className="validation-header">
        <h1>🔧 Panel de Entrenamiento de Modelos</h1>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
          <button 
            className="btn-run" 
            onClick={runTraining}
            disabled={training}
            title="Opcional: Personaliza los modelos entrenándolos con el dataset UCI Obesity"
          >
            {training ? 'Entrenando todos los modelos...' : 'Entrenar Todos los Modelos (MLP + XGBoost + RF + LR)'}
          </button>
          <small style={{ color: '#666', fontSize: '0.8rem', textAlign: 'right' }}>
            💡 Opcional: Personaliza los modelos con tus datos
          </small>
        </div>
      </header>
      
      {error && <div className="validation-error">{error}</div>}

      {!history || !history.has_history ? (
        <div className="stat-card" style={{ 
          padding: '20px', 
          background: '#e3f2fd', 
          borderLeft: '4px solid #2196f3',
          marginBottom: '20px'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#1976d2' }}>👋 Bienvenido al Entrenamiento de Modelos</h4>
          <p style={{ margin: '0', color: '#424242' }}>
            Esta sección te permite entrenar los modelos de Machine Learning con el dataset UCI Obesity.
            <br /><br />
            <strong>💡 Tip:</strong> Presiona el botón "Entrenar Todos los Modelos" para comenzar el entrenamiento de XGBoost, RandomForest y MLP.
            El entrenamiento es opcional - el sistema funciona con modelos pre-entrenados.
          </p>
        </div>
      ) : null}

      {datasetInfo && (
        <div className="validation-results">
          <div className="competitors-section">
            <h3>📊 Dataset</h3>
            <div className="stat-card">
              <p><strong>Fuente:</strong> {datasetInfo.source} | <strong>Registros:</strong> 2,111 | <strong>Características:</strong> {datasetInfo.num_features}</p>
            </div>
          </div>

          {hyperparameters && (
            <div className="competitors-section">
              <h3>⚙️ Configuración de Entrenamiento</h3>
              <div className="stat-card">
                <p><strong>MLP:</strong> {hyperparameters.max_epochs} epochs, batch {hyperparameters.batch_size}</p>
                <p><strong>Clásico:</strong> Grid search con cross-validation (cv=3)</p>
              </div>
            </div>
          )}

          {history && history.has_history && (
            <div className="competitors-section">
              <h3>📈 Historial</h3>
              <div className="stat-card">
                <p><strong>Entrenamientos:</strong> {history.total_runs} | <strong>Último:</strong> {history.last_updated ? new Date(history.last_updated).toLocaleDateString() : 'N/A'}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
