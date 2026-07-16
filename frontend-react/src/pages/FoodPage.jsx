import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';

function FoodPage() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const [foodName, setFoodName] = useState('');
  const [portion, setPortion] = useState(200);
  const [mealType, setMealType] = useState('lunch');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [saved, setSaved] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const mealTypes = [
    ['breakfast', '🥣', t('diary.breakfast')],
    ['lunch', '🥗', t('diary.lunch')],
    ['dinner', '🍽️', t('diary.dinner')],
    ['snack', '🍪', t('diary.snack')],
  ];

  const analyzeFood = async () => {
    if (!foodName.trim()) return;
    setAnalyzing(true);
    setResult(null);
    try {
      const res = await fetch(`/api/food/analyze?food_name=${encodeURIComponent(foodName)}&portion_grams=${portion}&meal_type=${mealType}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) setResult(data);
    } catch (e) { console.error(e); }
    setAnalyzing(false);
  };

  const logFood = async () => {
    if (!result) return;
    const n = result.nutrition?.nutrients || {};
    const res = await fetch(`/api/food/log?food_name=${encodeURIComponent(foodName)}&meal_type=${mealType}&calories=${n.calories || 0}&protein_g=${n.protein_g || 0}&carbs_g=${n.carbs_g || 0}&fats_g=${n.fats_g || 0}&portion_grams=${portion}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.message) { setSaved(true); setTimeout(() => { setSaved(false); setResult(null); setFoodName(''); }, 2000); }
  };

  const handleImageDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) analyzeImage(file);
  };

  const analyzeImage = async (file) => {
    setAnalyzing(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await fetch('/api/food/analyze?meal_type=' + mealType, {
        method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: fd
      });
      const data = await res.json();
      if (data.success && data.nutrition) {
        setResult(data);
        setFoodName(data.nutrition.food_name || file.name.replace(/\.[^.]+$/, ''));
      }
    } catch (e) { console.error(e); }
    setAnalyzing(false);
  };

  const c = (bg) => ({
    background: bg || 'var(--surface)', borderRadius: 16, padding: 18,
    border: '1px solid var(--border)', transition: 'all 0.15s'
  });
  const label = { fontSize: 12, fontWeight: 600, color: 'var(--text)', marginBottom: 4, display: 'block' };
  const input = {
    width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)',
    background: 'var(--surface-light)', color: 'var(--text)', fontSize: 14, boxSizing: 'border-box'
  };

  return (
    <div style={{ maxWidth: 700, animation: 'fadeIn 0.3s ease' }}>
      <h1 className="page-title">🍽️ {t('food.title')}</h1>
      <p className="page-subtitle">{t('food.subtitle')}</p>

      {saved && <div className="message success" style={{ marginBottom: 12 }}>✅ {t('food.savedCorrectly')}</div>}

      {/* Meal type selector */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {mealTypes.map(([key, icon, label]) => (
          <button key={key} onClick={() => setMealType(key)} style={{
            flex: 1, padding: '10px 8px', borderRadius: 12,
            border: `2px solid ${mealType === key ? 'var(--primary)' : 'var(--border)'}`,
            background: mealType === key ? 'rgba(79,70,229,0.06)' : 'var(--surface)',
            color: mealType === key ? 'var(--primary)' : 'var(--text)',
            fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s', textAlign: 'center'
          }}>
            <div style={{ fontSize: 20, marginBottom: 2 }}>{icon}</div>
            {label}
          </button>
        ))}
      </div>

      {/* Image upload zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleImageDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          ...c(dragOver ? 'rgba(79,70,229,0.04)' : 'var(--surface-light)'),
          border: `2px dashed ${dragOver ? 'var(--primary)' : 'var(--border)'}`,
          textAlign: 'center', padding: 32, cursor: 'pointer', marginBottom: 16,
          transition: 'all 0.2s'
        }}
      >
        <div style={{ fontSize: 36, marginBottom: 8 }}>📷</div>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{t('food.uploadImage')}</div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('food.dragImage')} — {t('food.orClick')}</div>
        <input ref={fileInputRef} type="file" accept="image/*" capture="environment"
          onChange={e => e.target.files?.[0] && analyzeImage(e.target.files[0])}
          style={{ display: 'none' }} />
      </div>

      {/* Manual input */}
      <div style={{ ...c('var(--surface)'), marginBottom: 16 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', margin: '0 0 12px' }}>
          ✏️ {t('food.addFood')}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 10 }}>
          <div>
            <label style={label}>{t('food.typeFood')}</label>
            <input type="text" value={foodName} onChange={e => setFoodName(e.target.value)}
              placeholder="Ej: pollo, arroz, ensalada..." style={input}
              onKeyDown={e => e.key === 'Enter' && analyzeFood()} />
          </div>
          <div>
            <label style={label}>{t('food.portionSize')}</label>
            <input type="number" min="10" max="2000" value={portion}
              onChange={e => setPortion(parseInt(e.target.value) || 200)} style={input} />
          </div>
        </div>
        <button onClick={analyzeFood} disabled={analyzing || !foodName.trim()} style={{
          marginTop: 12, padding: '10px 24px', borderRadius: 10, border: 'none',
          background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 700,
          cursor: 'pointer', opacity: analyzing || !foodName.trim() ? 0.5 : 1
        }}>
          {analyzing ? `⏳ ${t('food.analyzing')}` : `🤖 ${t('food.analyzePhoto')}`}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div style={{ ...c('var(--surface)'), animation: 'fadeIn 0.3s ease' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 20 }}>📊</span>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', margin: 0 }}>{t('food.result')}</h3>
            <span style={{
              fontSize: 9, padding: '2px 8px', borderRadius: 6,
              background: 'rgba(245,158,11,0.1)', color: 'var(--accent)', fontWeight: 700
            }}>
              🤖 {t('food.aiEstimation')}
            </span>
          </div>

          <div style={{ padding: '6px 10px', borderRadius: 8, background: 'rgba(245,158,11,0.06)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 14 }}>
            ⚠️ {t('food.aiNote')}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
            {[
              ['🔥', t('food.estimatedCalories'), `${result.nutrition?.nutrients?.calories || 0}`, 'kcal'],
              ['🥩', t('food.estimatedProtein'), `${result.nutrition?.nutrients?.protein_g || 0}`, 'g'],
              ['🍚', t('food.estimatedCarbs'), `${result.nutrition?.nutrients?.carbs_g || 0}`, 'g'],
              ['🥑', t('food.estimatedFats'), `${result.nutrition?.nutrients?.fats_g || 0}`, 'g'],
            ].map(([icon, lbl, val, unit]) => (
              <div key={lbl} style={{ textAlign: 'center', padding: '10px 4px', background: 'var(--surface-light)', borderRadius: 10 }}>
                <div style={{ fontSize: 20, marginBottom: 2 }}>{icon}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{lbl}</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text)' }}>{val}<span style={{ fontSize: 10, fontWeight: 500 }}>{unit}</span></div>
              </div>
            ))}
          </div>

          <button onClick={logFood} style={{
            width: '100%', padding: '12px 24px', borderRadius: 12, border: 'none',
            background: 'var(--secondary)', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer'
          }}>
            ✅ {t('food.confirmAndLog')}
          </button>
        </div>
      )}

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    </div>
  );
}

export default FoodPage;
