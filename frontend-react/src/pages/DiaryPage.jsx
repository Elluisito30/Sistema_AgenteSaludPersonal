import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';

function DiaryPage() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const [todayData, setTodayData] = useState(null);
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    water_liters: '', weight_kg: '', exercise_minutes: '', sleep_hours: '',
    mood: '', energy_level: '', stress_level: '', calories_consumed: '',
    notes: ''
  });

  useEffect(() => { loadDiary(); }, []);

  const loadDiary = async () => {
    setLoading(true);
    const [sumRes, histRes] = await Promise.all([
      apiRequest('/api/diary/summary', 'GET', null, token),
      apiRequest('/api/diary/history?days=7', 'GET', null, token)
    ]);
    if (sumRes.success) { setSummary(sumRes.data); setTodayData(sumRes.data?.today); }
    if (histRes.success) setHistory(histRes.data);
    setLoading(false);
  };

  const handleSave = async () => {
    const payload = {
      date: new Date().toISOString().split('T')[0],
      water_liters: form.water_liters ? parseFloat(form.water_liters) : null,
      weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
      exercise_minutes: form.exercise_minutes ? parseInt(form.exercise_minutes) : null,
      sleep_hours: form.sleep_hours ? parseFloat(form.sleep_hours) : null,
      mood: form.mood ? parseInt(form.mood) : null,
      energy_level: form.energy_level ? parseInt(form.energy_level) : null,
      stress_level: form.stress_level ? parseInt(form.stress_level) : null,
      calories_consumed: form.calories_consumed ? parseFloat(form.calories_consumed) : null,
      notes: form.notes || null,
    };
    const res = await apiRequest('/api/progress', 'POST', payload, token);
    if (res.success) { setSaved(true); loadDiary(); setShowAdd(false); setForm({}); setTimeout(() => setSaved(false), 3000); }
  };

  const c = (bg) => ({
    background: bg || 'var(--surface)', borderRadius: 14, padding: 16,
    border: '1px solid var(--border)', transition: 'all 0.15s'
  });
  const label = { fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 4, display: 'block' };
  const input = {
    width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border)',
    background: 'var(--surface-light)', color: 'var(--text)', fontSize: 13, boxSizing: 'border-box'
  };
  const moodEmoji = ['😢', '😟', '😐', '🙂', '😄'];
  const energyEmoji = ['🪫', '🔋', '⚡'];

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>{t('common.loading')}</div>
    </div>
  );

  return (
    <div className="page-full" style={{ animation: 'fadeIn 0.3s ease' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 className="page-title">📓 {t('diary.title')}</h1>
          <p className="page-subtitle" style={{ margin: 0 }}>{new Date().toLocaleDateString('es', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} style={{
          padding: '10px 20px', borderRadius: 12, border: 'none',
          background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer'
        }}>
          {showAdd ? '✕' : `➕ ${t('diary.addEntry')}`}
        </button>
      </div>

      {saved && <div className="message success" style={{ marginBottom: 12 }}>✅ {t('diary.saved')}</div>}

      {/* Add entry form */}
      {showAdd && (
        <div style={{ ...c('var(--surface)'), marginBottom: 16, animation: 'fadeIn 0.2s ease' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, margin: '0 0 14px', color: 'var(--text)' }}>
            ➕ {t('diary.addEntry')}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
            <div>
              <label style={label}>💧 {t('diary.water')} (L)</label>
              <input type="number" step="0.1" min="0" value={form.water_liters || ''}
                onChange={e => setForm(f => ({ ...f, water_liters: e.target.value }))} style={input} placeholder="0.5" />
            </div>
            <div>
              <label style={label}>⚖️ {t('diary.weight')}</label>
              <input type="number" step="0.1" min="30" max="250" value={form.weight_kg || ''}
                onChange={e => setForm(f => ({ ...f, weight_kg: e.target.value }))} style={input} placeholder="70" />
            </div>
            <div>
              <label style={label}>🏃 {t('diary.exercise')} (min)</label>
              <input type="number" min="0" value={form.exercise_minutes || ''}
                onChange={e => setForm(f => ({ ...f, exercise_minutes: e.target.value }))} style={input} placeholder="30" />
            </div>
            <div>
              <label style={label}>🔥 {t('diary.caloriesConsumed')}</label>
              <input type="number" min="0" value={form.calories_consumed || ''}
                onChange={e => setForm(f => ({ ...f, calories_consumed: e.target.value }))} style={input} placeholder="2000" />
            </div>
            <div>
              <label style={label}>😴 {t('diary.sleep')}</label>
              <input type="number" step="0.5" min="0" max="24" value={form.sleep_hours || ''}
                onChange={e => setForm(f => ({ ...f, sleep_hours: e.target.value }))} style={input} placeholder="7" />
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <label style={label}>😊 {t('diary.mood')}</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {moodEmoji.map((em, i) => (
                <button key={i} onClick={() => setForm(f => ({ ...f, mood: i + 1 }))}
                  style={{
                    fontSize: 24, padding: '6px 10px', borderRadius: 10, border: `2px solid ${form.mood === i + 1 ? 'var(--primary)' : 'var(--border)'}`,
                    background: form.mood === i + 1 ? 'rgba(79,70,229,0.08)' : 'var(--surface)',
                    cursor: 'pointer', transition: 'all 0.15s'
                  }}>{em}</button>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <label style={label}>⚡ {t('diary.energy')}</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {energyEmoji.map((em, i) => (
                <button key={i} onClick={() => setForm(f => ({ ...f, energy_level: i + 1 }))}
                  style={{
                    fontSize: 22, padding: '6px 12px', borderRadius: 10, border: `2px solid ${form.energy_level === i + 1 ? 'var(--primary)' : 'var(--border)'}`,
                    background: form.energy_level === i + 1 ? 'rgba(79,70,229,0.08)' : 'var(--surface)',
                    cursor: 'pointer', transition: 'all 0.15s'
                  }}>{em}</button>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <label style={label}>📝 {t('diary.notes')}</label>
            <textarea value={form.notes || ''} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              placeholder={t('diary.notesPlaceholder')} rows={2}
              style={{ ...input, resize: 'vertical', fontFamily: 'inherit' }} />
          </div>

          <button onClick={handleSave} style={{
            marginTop: 14, padding: '10px 24px', borderRadius: 10, border: 'none',
            background: 'var(--secondary)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer'
          }}>💾 {t('diary.saveEntry')}</button>
        </div>
      )}

      {/* Daily Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 16 }}>
        {[
          ['💧', t('diary.totalWater'), `${summary?.today?.water_liters || 0}L`],
          ['🔥', t('diary.totalCalories'), `${summary?.today?.calories_consumed || 0}`],
          ['🏃', t('diary.totalExercise'), `${summary?.today?.exercise_minutes || 0}min`],
          ['😴', t('diary.sleep'), `${summary?.today?.sleep_hours || 0}h`],
        ].map(([icon, lbl, val]) => (
          <div key={lbl} style={{ ...c('var(--surface)'), textAlign: 'center', padding: 14 }}>
            <div style={{ fontSize: 20, marginBottom: 2 }}>{icon}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{lbl}</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)' }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Timeline */}
      <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', margin: '0 0 12px' }}>
        📅 {t('diary.timeline')}
      </h3>
      {history.length === 0 ? (
        <div style={{ ...c('var(--surface)'), textAlign: 'center', padding: 32, color: 'var(--text-muted)', fontSize: 13 }}>
          {t('diary.noEntries')}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {history.map((entry, i) => (
            <div key={i} style={{ ...c('var(--surface)'), display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{
                width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                background: 'var(--primary)'
              }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
                  {new Date(entry.date).toLocaleDateString('es', { weekday: 'short', month: 'short', day: 'numeric' })}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {entry.water_liters && <span>💧 {entry.water_liters}L</span>}
                  {entry.calories_consumed && <span>🔥 {entry.calories_consumed}kcal</span>}
                  {entry.exercise_minutes && <span>🏃 {entry.exercise_minutes}min</span>}
                  {entry.weight_kg && <span>⚖️ {entry.weight_kg}kg</span>}
                  {entry.sleep_hours && <span>😴 {entry.sleep_hours}h</span>}
                  {entry.mood && <span>{moodEmoji[entry.mood - 1] || '😐'}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    </div>
  );
}

export default DiaryPage;
