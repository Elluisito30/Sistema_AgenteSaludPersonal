import { useTranslation } from 'react-i18next';

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const currentLang = i18n.language?.substring(0, 2) || 'es';

  const switchLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('healthai-lang', lng);
  };

  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
      <button
        onClick={() => switchLanguage('es')}
        style={{
          padding: '4px 8px',
          borderRadius: '6px',
          border: 'none',
          cursor: 'pointer',
          fontSize: '12px',
          fontWeight: currentLang === 'es' ? '700' : '500',
          background: currentLang === 'es' ? 'var(--brand)' : 'transparent',
          color: currentLang === 'es' ? '#fff' : 'var(--text-secondary)',
          transition: 'all 0.2s'
        }}
        title={t('reports.spanish')}
      >
        ES
      </button>
      <button
        onClick={() => switchLanguage('en')}
        style={{
          padding: '4px 8px',
          borderRadius: '6px',
          border: 'none',
          cursor: 'pointer',
          fontSize: '12px',
          fontWeight: currentLang === 'en' ? '700' : '500',
          background: currentLang === 'en' ? 'var(--brand)' : 'transparent',
          color: currentLang === 'en' ? '#fff' : 'var(--text-secondary)',
          transition: 'all 0.2s'
        }}
        title={t('reports.english')}
      >
        EN
      </button>
    </div>
  );
}
