import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';

const STEPS = ['welcome', 'physical', 'activity', 'goals', 'habits', 'food', 'summary'];

const STEP_ICONS = ['👋', '📏', '🏃', '🎯', '💤', '🥗', '✅'];

const GOAL_I18N_KEYS = {
  weight_loss: 'weightLoss',
  muscle_gain: 'muscleGain',
  better_sleep: 'betterSleep',
  stress_reduction: 'stressReduction',
  energy_boost: 'energyBoost',
  general_wellness: 'generalWellness',
};

const ACTIVITY_I18N_KEYS = {
  sedentary: 'sedentary',
  light: 'light',
  moderate: 'moderate',
  active: 'active',
  very_active: 'veryActive',
  veryActive: 'veryActive',
};

function OnboardingPage() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    age: '', gender: '', height_cm: '', weight_kg: '',
    activity_level: '', sleep_hours: 7, smokes: false,
    family_history: false, health_goals: [],
    favc: 'Sometimes', fcvc: 2, ch2o: 2,
  });

  const update = (field, value) => setData(prev => ({ ...prev, [field]: value }));

  const toggleGoal = (goal) => {
    setData(prev => ({
      ...prev,
      health_goals: prev.health_goals.includes(goal)
        ? prev.health_goals.filter(g => g !== goal)
        : [...prev.health_goals, goal]
    }));
  };

  const next = () => setStep(s => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep(s => Math.max(s - 1, 0));

  const normalizeActivityLevel = (level) => {
    if (level === 'veryActive') return 'very_active';
    return level || 'moderate';
  };

  const handleFinish = async () => {
    setSaving(true);
    setError(null);
    const payload = {
      age: parseInt(data.age) || 30,
      gender: data.gender || 'male',
      height_cm: parseFloat(data.height_cm) || 170,
      weight_kg: parseFloat(data.weight_kg) || 70,
      activity_level: normalizeActivityLevel(data.activity_level),
      sleep_hours: data.sleep_hours || 7,
      smokes: data.smokes,
      has_chronic_conditions: false,
      health_goals: data.health_goals,
      family_history: data.family_history,
      favc: data.favc,
      fcvc: data.fcvc,
      ch2o: data.ch2o,
    };
    const res = await apiRequest('/api/profile', 'POST', payload, token);
    if (res.success) {
      navigate('/dashboard');
    } else {
      setError(res.error || t('onboarding.errorSaving'));
    }
    setSaving(false);
  };

  const goalLabel = (goal) => t(`onboarding.${GOAL_I18N_KEYS[goal] || goal}`);
  const activityLabel = (level) => t(`onboarding.${ACTIVITY_I18N_KEYS[level] || level}`);

  const s = step;
  const cardStyle = {
    background: 'var(--surface)', borderRadius: 20, padding: '32px 28px',
    maxWidth: 480, width: '100%', boxShadow: 'var(--shadow-lg)',
    border: '1px solid var(--border)', animation: 'fadeIn 0.3s ease'
  };
  const labelStyle = { fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 6, display: 'block' };
  const inputStyle = {
    width: '100%', padding: '10px 14px', borderRadius: 10,
    border: '1px solid var(--border)', background: 'var(--surface-light)',
    color: 'var(--text)', fontSize: 14, boxSizing: 'border-box'
  };
  const selectStyle = { ...inputStyle, appearance: 'auto' };
  const btnPrimary = {
    padding: '12px 28px', borderRadius: 12, border: 'none',
    background: 'var(--primary)', color: '#fff', fontSize: 14,
    fontWeight: 700, cursor: 'pointer', transition: 'all 0.15s'
  };
  const btnSecondary = {
    padding: '12px 28px', borderRadius: 12,
    border: '1px solid var(--border)', background: 'var(--surface)',
    color: 'var(--text)', fontSize: 14, fontWeight: 500, cursor: 'pointer'
  };
  const goalChip = (active) => ({
    padding: '10px 16px', borderRadius: 12, border: `2px solid ${active ? 'var(--primary)' : 'var(--border)'}`,
    background: active ? 'rgba(79,70,229,0.08)' : 'var(--surface)',
    color: active ? 'var(--primary)' : 'var(--text)', fontSize: 13,
    fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s', textAlign: 'center'
  });

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 24, background: 'var(--background)' }}>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, fontWeight: 600 }}>
        {t('onboarding.step')} {step + 1} {t('onboarding.of')} {STEPS.length}
      </div>
      <div style={{ display: 'flex', gap: 6, marginBottom: 24 }}>
        {STEPS.map((_, i) => (
          <div key={i} style={{
            width: i <= step ? 32 : 8, height: 4, borderRadius: 2,
            background: i <= step ? 'var(--primary)' : 'var(--border)',
            transition: 'all 0.3s ease'
          }} />
        ))}
      </div>

      <div style={cardStyle}>
        <div style={{ textAlign: 'center', fontSize: 40, marginBottom: 12 }}>{STEP_ICONS[s]}</div>
        <h2 style={{ textAlign: 'center', fontSize: 20, fontWeight: 800, color: 'var(--text)', margin: '0 0 6px' }}>
          {t(`onboarding.${STEPS[s]}Title`)}
        </h2>
        <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)', margin: '0 0 24px', lineHeight: 1.5 }}>
          {t(`onboarding.${STEPS[s]}Desc`)}
        </p>

        {/* Step 0: Welcome */}
        {s === 0 && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <p style={{ fontSize: 14, color: 'var(--text-muted)', lineHeight: 1.6 }}>
              {t('onboarding.welcomeDesc')}
            </p>
          </div>
        )}

        {/* Step 1: Physical */}
        {s === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={labelStyle}>{t('onboarding.age')}</label>
              <input type="number" min="10" max="120" value={data.age}
                onChange={e => update('age', e.target.value)} style={inputStyle} placeholder="25" />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>{t('onboarding.height')}</label>
                <input type="number" min="100" max="230" step="0.1" value={data.height_cm}
                  onChange={e => update('height_cm', e.target.value)} style={inputStyle} placeholder="170" />
              </div>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>{t('onboarding.weight')}</label>
                <input type="number" min="30" max="250" step="0.1" value={data.weight_kg}
                  onChange={e => update('weight_kg', e.target.value)} style={inputStyle} placeholder="70" />
              </div>
            </div>
            <div>
              <label style={labelStyle}>{t('onboarding.gender')}</label>
              <div style={{ display: 'flex', gap: 10 }}>
                {['male', 'female'].map(g => (
                  <button key={g} onClick={() => update('gender', g)}
                    style={{ ...goalChip(data.gender === g), flex: 1 }}>
                    {g === 'male' ? '👨' : '👩'} {t(`onboarding.${g}`)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Activity */}
        {s === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {['sedentary', 'light', 'moderate', 'active', 'veryActive'].map(level => {
              const icons = { sedentary: '🪑', light: '🚶', moderate: '🚴', active: '🏃', veryActive: '🏋️' };
              return (
                <button key={level} onClick={() => update('activity_level', level)}
                  style={goalChip(data.activity_level === level)}>
                  {icons[level]} {t(`onboarding.${level}`)}
                </button>
              );
            })}
          </div>
        )}

        {/* Step 3: Goals */}
        {s === 3 && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              ['weight_loss', '📉'], ['muscle_gain', '💪'], ['better_sleep', '😴'],
              ['stress_reduction', '🧘'], ['energy_boost', '⚡'], ['general_wellness', '🌟']
            ].map(([goal, icon]) => (
              <button key={goal} onClick={() => toggleGoal(goal)}
                style={goalChip(data.health_goals.includes(goal))}>
                {icon} {goalLabel(goal)}
              </button>
            ))}
          </div>
        )}

        {/* Step 4: Habits */}
        {s === 4 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={labelStyle}>{t('onboarding.sleepHours')}: {data.sleep_hours}</label>
              <input type="range" min="4" max="12" value={data.sleep_hours}
                onChange={e => update('sleep_hours', parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--primary)' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
                <span>4h</span><span>12h</span>
              </div>
            </div>
            <div>
              <label style={labelStyle}>{t('onboarding.smoker')}</label>
              <div style={{ display: 'flex', gap: 10 }}>
                {[true, false].map(v => (
                  <button key={String(v)} onClick={() => update('smokes', v)}
                    style={{ ...goalChip(data.smokes === v), flex: 1 }}>
                    {v ? t('onboarding.yes') : t('onboarding.no')}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label style={labelStyle}>{t('onboarding.familyHistory')}</label>
              <div style={{ display: 'flex', gap: 10 }}>
                {[true, false].map(v => (
                  <button key={String(v)} onClick={() => update('family_history', v)}
                    style={{ ...goalChip(data.family_history === v), flex: 1 }}>
                    {v ? t('onboarding.yes') : t('onboarding.no')}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Food preferences */}
        {s === 5 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={labelStyle}>{t('onboarding.fastFood')}</label>
              <select value={data.favc} onChange={e => update('favc', e.target.value)} style={selectStyle}>
                <option value="Always">{t('profile.fastFoodAlways')}</option>
                <option value="Frequently">{t('profile.fastFoodFrequently')}</option>
                <option value="Sometimes">{t('profile.fastFoodSometimes')}</option>
                <option value="No">{t('profile.fastFoodNo')}</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>{t('onboarding.vegetables')}: {data.fcvc}</label>
              <input type="range" min="1" max="3" step="1" value={data.fcvc}
                onChange={e => update('fcvc', parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--primary)' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
                <span>1</span><span>2</span><span>3</span>
              </div>
            </div>
            <div>
              <label style={labelStyle}>{t('onboarding.water')}</label>
              <div style={{ display: 'flex', gap: 10 }}>
                {[1, 2, 3].map(v => (
                  <button key={v} onClick={() => update('ch2o', v)}
                    style={{ ...goalChip(data.ch2o === v), flex: 1 }}>
                    {v === 1 ? '< 1L' : v === 2 ? '1-2L' : '2L+'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 6: Summary */}
        {s === 6 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
            {[
              ['👤', `${data.age || '?'} ${t('onboarding.years')}, ${data.gender === 'male' ? t('onboarding.male') : t('onboarding.female')}`],
              ['📏', `${data.height_cm || '?'} cm, ${data.weight_kg || '?'} kg`],
              ['🏃', activityLabel(data.activity_level || 'moderate')],
              ['😴', `${data.sleep_hours}h ${t('onboarding.sleepLabel')}`],
              ['🎯', data.health_goals.length ? data.health_goals.map(goalLabel).join(', ') : t('onboarding.noGoalsSelected')],
              ['🥗', `${t('onboarding.fastFood')}: ${data.favc}, ${t('onboarding.vegetables')}: ${data.fcvc}, ${t('onboarding.water')}: ${data.ch2o}`],
            ].map(([icon, text], i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'var(--surface-light)', borderRadius: 10 }}>
                <span style={{ fontSize: 18 }}>{icon}</span>
                <span style={{ color: 'var(--text)' }}>{text}</span>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 10, background: 'rgba(239,68,68,0.08)', color: 'var(--danger)', fontSize: 13 }}>
            {error}
          </div>
        )}

        {/* Navigation buttons */}
        <div style={{ display: 'flex', justifyContent: s === 0 ? 'center' : 'space-between', marginTop: 24, gap: 12 }}>
          {s > 0 && (
            <button onClick={back} style={btnSecondary}>{t('common.back')}</button>
          )}
          {s === 0 ? (
            <button onClick={next} style={btnPrimary}>{t('onboarding.startBtn')}</button>
          ) : s < STEPS.length - 1 ? (
            <button onClick={next} style={btnPrimary}>{t('common.next')}</button>
          ) : (
            <button onClick={handleFinish} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.6 : 1 }}>
              {saving ? t('onboarding.analyzing') : `✅ ${t('onboarding.startBtn')}`}
            </button>
          )}
        </div>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

export default OnboardingPage;
