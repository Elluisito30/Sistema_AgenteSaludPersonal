import { useTranslation } from 'react-i18next';
import Plot from 'react-plotly.js';

function ExplainabilityCenter({ analysis, latestPrediction, importanceData }) {
  const { t } = useTranslation();

  if (!analysis) {
    return (
      <div className="tab-panel">
        <div className="empty-state">
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
          <h3>{t('explainability.title')}</h3>
          <p>{t('explainability.noData')}</p>
        </div>
      </div>
    );
  }

  const features = importanceData?.features || [
    { feature: 'Age', importance: 0.18 },
    { feature: 'Weight', importance: 0.16 },
    { feature: 'Height', importance: 0.14 },
    { feature: 'FAF (Activity)', importance: 0.12 },
    { feature: 'FCVC (Vegetables)', importance: 0.10 },
    { feature: 'CH2O (Water)', importance: 0.09 },
    { feature: 'FAVC (Fast Food)', importance: 0.08 },
    { feature: 'Gender', importance: 0.06 },
    { feature: 'SMOKE', importance: 0.04 },
    { feature: 'Family History', importance: 0.02 },
    { feature: 'CALC (Alcohol)', importance: 0.01 }
  ];

  const xai = analysis.xai || {};
  const score = analysis.health_score || analysis.healthScore || 0;
  const bmi = analysis.bmi || 0;
  const mlPred = latestPrediction || {};

  const workflowSteps = [
    { icon: '📥', titleKey: 'explainability.dataInput', descKey: 'explainability.dataInputDesc', color: 'var(--brand)' },
    { icon: '🤖', titleKey: 'explainability.mlProcessing', descKey: 'explainability.mlProcessingDesc', color: '#8b5cf6' },
    { icon: '⚕️', titleKey: 'explainability.clinicalRules', descKey: 'explainability.clinicalRulesDesc', color: '#10b981' },
    { icon: '📊', titleKey: 'explainability.finalOutput', descKey: 'explainability.finalOutputDesc', color: '#f59e0b' }
  ];

  return (
    <div className="tab-panel explainability-panel">
      <div className="section-header">
        <h2>🔍 {t('explainability.title')}</h2>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>{t('explainability.subtitle')}</p>
      </div>

      <div className="workflow-steps">
        {workflowSteps.map((step, i) => (
          <div key={i} className="workflow-step">
            <div className="workflow-step-icon" style={{ background: step.color }}>{step.icon}</div>
            <div className="workflow-step-content">
              <h4>{t(step.titleKey)}</h4>
              <p>{t(step.descKey)}</p>
            </div>
            {i < workflowSteps.length - 1 && <div className="workflow-arrow">→</div>}
          </div>
        ))}
      </div>

      <div className="explain-grid">
        <div className="explain-card">
          <h3>📈 {t('explainability.featureImportance')}</h3>
          <Plot
            data={[{
              type: 'bar',
              orientation: 'h',
              y: features.map(f => f.feature).reverse(),
              x: features.map(f => f.importance).reverse(),
              marker: {
                color: features.map((_, i) => {
                  const ratio = i / features.length;
                  return ratio < 0.3 ? 'var(--brand)' : ratio < 0.6 ? 'var(--success)' : 'var(--text-secondary)';
                }).reverse()
              },
              hovertemplate: '%{y}: %{x:.1%}<extra></extra>'
            }]}
            layout={{
              height: 350,
              margin: { l: 120, r: 20, t: 10, b: 30 },
              xaxis: { title: 'Importance', tickformat: '.0%', gridcolor: 'var(--border)' },
              yaxis: { gridcolor: 'transparent' },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { color: 'var(--text)' }
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        </div>

        <div className="explain-card">
          <h3>🎯 {t('explainability.predictionConfidence')}</h3>
          <div className="confidence-section">
            <div className="confidence-meter">
              <div className="confidence-label">
                <span>{t('predictions.confidence')}</span>
                <span style={{ fontWeight: 700 }}>{mlPred.confidence || '95%'}</span>
              </div>
              <div className="confidence-bar-bg">
                <div
                  className="confidence-bar-fill"
                  style={{
                    width: mlPred.confidence_value ? `${mlPred.confidence_value * 100}%` : '95%',
                    background: 'linear-gradient(90deg, var(--brand), var(--success))'
                  }}
                />
              </div>
            </div>

            <div className="confidence-factors">
              <div className="factor-item">
                <span className="factor-dot" style={{ background: 'var(--brand)' }}></span>
                <span>{t('analysis.healthScore')}: <strong>{score}/100</strong></span>
              </div>
              <div className="factor-item">
                <span className="factor-dot" style={{ background: 'var(--success)' }}></span>
                <span>{t('analysis.bmi')}: <strong>{bmi?.toFixed(1) || 'N/A'}</strong></span>
              </div>
              <div className="factor-item">
                <span className="factor-dot" style={{ background: '#8b5cf6' }}></span>
                <span>{t('predictions.predictedClass')}: <strong>{mlPred.predicted_category || mlPred.predictedCategory || 'N/A'}</strong></span>
              </div>
            </div>
          </div>
        </div>

        <div className="explain-card full-width">
          <h3>⚕️ {t('explainability.clinicalFactors')}</h3>
          <div className="clinical-factors-grid">
            {xai.main_reason && (
              <div className="clinical-factor">
                <span className="factor-icon">💡</span>
                <div>
                  <strong>{t('xai.mainReason')}</strong>
                  <p>{xai.main_reason}</p>
                </div>
              </div>
            )}
            {xai.risk_explanation && (
              <div className="clinical-factor">
                <span className="factor-icon">⚠️</span>
                <div>
                  <strong>{t('xai.riskExplanation')}</strong>
                  <p>{xai.risk_explanation}</p>
                </div>
              </div>
            )}
            {xai.summary && (
              <div className="clinical-factor">
                <span className="factor-icon">📋</span>
                <div>
                  <strong>{t('xai.summary')}</strong>
                  <p>{xai.summary}</p>
                </div>
              </div>
            )}
            {!xai.main_reason && !xai.risk_explanation && !xai.summary && (
              <div className="clinical-factor">
                <span className="factor-icon">ℹ️</span>
                <div>
                  <p>{t('explainability.personalInsight')}</p>
                  <p>Health Score: {score}/100 | BMI: {bmi?.toFixed(1)}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExplainabilityCenter;
