import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { useAnalysis } from '../components/layout/AppLayout';

function ProfilePage() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const { loadAnalysis } = useAnalysis();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [sleepHours, setSleepHours] = useState(7);

  useEffect(() => { loadProfile(); }, []);

  const loadProfile = async () => {
    setLoading(true);
    const res = await apiRequest('/api/profile', 'GET', null, token);
    if (res.success) { setProfile(res.data); setSleepHours(res.data.sleep_hours || 7); }
    setLoading(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    const goalsSelect = e.target.healthGoals;
    const goals = goalsSelect ? Array.from(goalsSelect.selectedOptions).map(o => o.value) : [];
    const data = {
      age: parseInt(e.target.age.value), gender: e.target.gender.value,
      height_cm: parseFloat(e.target.height.value), weight_kg: parseFloat(e.target.weight.value),
      activity_level: e.target.activityLevel.value, sleep_hours: sleepHours,
      smokes: e.target.smokes.checked, has_chronic_conditions: e.target.hasChronic?.checked || false,
      chronic_conditions_detail: e.target.chronicDetail?.value || '',
      health_goals: goals, family_history: e.target.familyHistory?.checked || false,
      favc: e.target.favc?.value || 'Sometimes', fcvc: parseFloat(e.target.fcvc?.value || 2),
      ch2o: parseFloat(e.target.ch2o?.value || 2),
    };
    const res = await apiRequest('/api/profile', 'POST', data, token);
    if (res.success) {
      setMessage({ type: 'success', text: t('profilePage.saved') });
      setProfile(data);
      try { await loadAnalysis(); } catch (_) { /* optional */ }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      setMessage({ type: 'error', text: res.error || t('common.error') });
    }
    setSaving(false);
    setTimeout(() => setMessage(null), 5000);
  };

  const section = (title) => ({
    fontSize: 14, fontWeight: 700, color: 'var(--text)', margin: '20px 0 12px',
    paddingBottom: 8, borderBottom: '1px solid var(--border)'
  });
  const label = { fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4, display: 'block' };
  const input = {
    width: '100%', padding: '9px 12px', borderRadius: 10, border: '1px solid var(--border)',
    background: 'var(--surface-light)', color: 'var(--text)', fontSize: 13, boxSizing: 'border-box'
  };

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>{t('common.loading')}</div>
    </div>
  );

  return (
    <div className="page-full" style={{ animation: 'fadeIn 0.3s ease' }}>
      <h1 className="page-title">👤 {t('profilePage.title')}</h1>
      <p className="page-subtitle">{t('profilePage.subtitle')}</p>

      {message && (
        <div
          role="status"
          style={{
            marginBottom: 16,
            padding: '14px 18px',
            borderRadius: 12,
            fontSize: 14,
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: message.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
            color: message.type === 'success' ? '#059669' : '#dc2626',
            border: `1px solid ${message.type === 'success' ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
          }}
        >
          <span>{message.type === 'success' ? '✅' : '✕'}</span>
          {message.text}
        </div>
      )}

      <form onSubmit={handleSave} style={{
        background: 'var(--surface)', borderRadius: 16, padding: 24,
        border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={section(t('profilePage.personalData'))}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={label}>{t('onboarding.age')}</label>
              <input type="number" name="age" defaultValue={profile?.age || ''} min="10" max="120" style={input} required />
            </div>
            <div>
              <label style={label}>{t('onboarding.gender')}</label>
              <select name="gender" defaultValue={profile?.gender || ''} style={input} required>
                <option value="">{t('profile.choose')}</option>
                <option value="male">{t('profile.male')}</option>
                <option value="female">{t('profile.female')}</option>
              </select>
            </div>
            <div>
              <label style={label}>{t('onboarding.height')}</label>
              <input type="number" name="height" step="0.1" defaultValue={profile?.height_cm || ''} min="100" max="230" style={input} required />
            </div>
            <div>
              <label style={label}>{t('onboarding.weight')}</label>
              <input type="number" name="weight" step="0.1" defaultValue={profile?.weight_kg || ''} min="30" max="250" style={input} required />
            </div>
          </div>
        </div>

        <div style={section(t('profilePage.lifestyle'))}>
          <div style={{ marginBottom: 12 }}>
            <label style={label}>{t('profile.activityLevel')}</label>
            <select name="activityLevel" defaultValue={profile?.activity_level || ''} style={input} required>
              <option value="">{t('profile.choose')}</option>
              <option value="sedentary">{t('profile.sedentary')}</option>
              <option value="light">{t('profile.light')}</option>
              <option value="moderate">{t('profile.moderate')}</option>
              <option value="active">{t('profile.active')}</option>
              <option value="very_active">{t('profile.veryActive')}</option>
            </select>
          </div>
          <div>
            <label style={label}>{t('onboarding.sleepHours')}: {sleepHours}h</label>
            <input type="range" min="4" max="12" value={sleepHours}
              onChange={e => setSleepHours(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--primary)' }} />
          </div>
        </div>

        <div style={section(t('profilePage.health'))}>
          <label style={{ ...label, display: 'flex', alignItems: 'center', gap: 8 }}>
            <input type="checkbox" name="smokes" defaultChecked={profile?.smokes} />
            {t('profile.smoker')}
          </label>
          <label style={{ ...label, display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
            <input type="checkbox" name="hasChronic" defaultChecked={profile?.has_chronic_conditions} />
            {t('profile.chronicConditions')}
          </label>
          <label style={{ ...label, display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
            <input type="checkbox" name="familyHistory" defaultChecked={profile?.family_history} />
            {t('profile.familyHistory')}
          </label>
        </div>

        <div style={section(t('profilePage.nutrition'))}>
          <div style={{ marginBottom: 12 }}>
            <label style={label}>{t('profile.fastFood')}</label>
            <select name="favc" defaultValue={profile?.favc || 'Sometimes'} style={input}>
              <option value="Always">{t('profile.fastFoodAlways')}</option>
              <option value="Frequently">{t('profile.fastFoodFrequently')}</option>
              <option value="Sometimes">{t('profile.fastFoodSometimes')}</option>
              <option value="No">{t('profile.fastFoodNo')}</option>
            </select>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={label}>{t('profile.vegetables')}</label>
            <select name="fcvc" defaultValue={profile?.fcvc || 2} style={input}>
              <option value="1">{t('profile.veg1')}</option>
              <option value="2">{t('profile.veg2')}</option>
              <option value="3">{t('profile.veg3')}</option>
            </select>
          </div>
          <div>
            <label style={label}>{t('profile.water')}</label>
            <select name="ch2o" defaultValue={profile?.ch2o || 2} style={input}>
              <option value="1">{t('profile.water1')}</option>
              <option value="2">{t('profile.water2')}</option>
              <option value="3">{t('profile.water3')}</option>
            </select>
          </div>
        </div>

        <div style={section(t('profilePage.goals'))}>
          <select name="healthGoals" multiple defaultValue={profile?.health_goals || []} size="5" style={{ ...input, height: 'auto' }}>
            <option value="weight_loss">{t('goals.weightLoss')}</option>
            <option value="muscle_gain">{t('goals.muscleGain')}</option>
            <option value="better_sleep">{t('goals.betterSleep')}</option>
            <option value="stress_reduction">{t('goals.stressReduction')}</option>
            <option value="energy_boost">{t('goals.energyBoost')}</option>
            <option value="general_wellness">{t('goals.generalWellness')}</option>
          </select>
        </div>

        <button type="submit" disabled={saving} style={{
          width: '100%', padding: '12px 24px', borderRadius: 12, border: 'none',
          background: 'var(--primary)', color: '#fff', fontSize: 14, fontWeight: 700,
          cursor: 'pointer', marginTop: 20, opacity: saving ? 0.6 : 1
        }}>
          {saving ? t('common.loading') : `💾 ${t('profilePage.save')}`}
        </button>
      </form>

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    </div>
  );
}

export default ProfilePage;
