import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/api';
import t from '../i18n/IT.json';

export default function Login() {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showChoice, setShowChoice] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await api.login(token);
      if (user.role === 'super_user') {
        setShowChoice(true);
      } else {
        navigate('/user');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (showChoice) {
    return (
      <div className="container">
        <div className="login-card glass fade-in" style={{ textAlign: 'center' }}>
          <h1 style={{ marginBottom: '1rem' }}>{t.login.choiceTitle}</h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2.5rem', fontSize: '0.9rem' }}>
            {t.login.choiceDescription}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <button 
              className="btn-primary" 
              onClick={() => navigate('/admin')}
            >
              {t.login.goToAdmin}
            </button>
            <button 
              className="btn-outline" 
              onClick={() => navigate('/user')}
            >
              {t.login.goToVote}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="login-card glass fade-in">
        <h1 style={{ marginBottom: '0.5rem' }}>{t.login.title}</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2.5rem', fontSize: '0.9rem' }}>
          {t.login.subtitle}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="token">{t.login.tokenLabel}</label>
            <input
              id="token"
              type="text"
              placeholder={t.login.tokenPlaceholder}
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
              autoComplete="off"
            />
          </div>

          {error && (
            <p style={{ color: 'var(--danger)', fontSize: '0.8rem', marginBottom: '1rem' }}>
              {error}
            </p>
          )}

          <button 
            type="submit" 
            className="btn-primary" 
            disabled={loading}
          >
            {loading ? t.login.loading : t.login.submit}
          </button>
        </form>

        <div style={{ marginTop: '2rem', fontSize: '0.75rem', color: 'rgba(255,255,255,0.2)' }}>
          {t.login.footer}
        </div>
      </div>
    </div>
  );
}
