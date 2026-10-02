import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { tenantApi } from '../api/resources';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, selectTenant } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      const tenants = await tenantApi.myTenants();
      if (tenants.length > 0) {
        selectTenant(tenants[0].tenant_id);
      }
      navigate("/");
    } catch (err) {
      setError(err.data?.detail || err.message || "Incorrect email or password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
      <div style={{ width: '100%', maxWidth: 380 }}>
        <p style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 500, color: 'var(--moss)', margin: '0 0 2.5rem' }}>
          Ledger
        </p>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 34, fontWeight: 500, lineHeight: 1.25, margin: '0 0 0.5rem', maxWidth: '15ch' }}>
          Keep every lead moving.
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: 15, margin: '0 0 2.25rem' }}>Sign in to your team's workspace.</p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="email">Work email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="error-text">{error}</p>}
          <button className="btn-primary" style={{ width: '100%', marginTop: 8 }} disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p style={{ marginTop: '1.5rem', fontSize: 13, color: 'var(--muted)' }}>
          New team? <Link to="/register" style={{ color: 'var(--moss)', fontWeight: 500 }}>Create a workspace</Link>
        </p>
      </div>
    </div>
  );
}
