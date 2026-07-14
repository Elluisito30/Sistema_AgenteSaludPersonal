import { useTheme } from '../contexts/ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      title={isDark ? 'Modo Claro' : 'Modo Oscuro'}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '36px',
        height: '36px',
        borderRadius: '10px',
        border: '1px solid var(--border)',
        background: 'var(--surface)',
        cursor: 'pointer',
        fontSize: '18px',
        transition: 'all 0.3s',
        color: 'var(--text)',
        flexShrink: 0
      }}
    >
      {isDark ? '☀️' : '🌙'}
    </button>
  );
}
