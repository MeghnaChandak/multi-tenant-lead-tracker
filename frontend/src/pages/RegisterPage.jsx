import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, tenantApi } from '../api/resources';
import { useAuth } from '../hooks/useAuth';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [workspaceName, setWorkspaceName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, selectTenant } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authApi.register(email, password);
      await login(email, password);
      const tenant = await tenantApi.create(workspaceName);
      selectTenant(tenant.id);
      navigate('/');
    } catch (err) {
      setError(err.data?.detail || 'Could not create your account');
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
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 500, lineHeight: 1.25, margin: '0 0 1.75rem' }}>
          Set up your workspace.
        </h1>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="workspace">Workspace name</label>
            <input id="workspace" value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} placeholder="Acme Sales Co" required />
          </div>
          <div className="field">
            <label htmlFor="email">Work email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
          </div>
          {error && <p className="error-text">{error}</p>}
          <button className="btn-primary" style={{ width: '100%', marginTop: 8 }} disabled={loading}>
            {loading ? 'Creating…' : 'Create workspace'}
          </button>
        </form>
      </div>
    </div>
  );
}
