import { useEffect, useState } from 'react';
import { billingApi } from '../api/resources';
import { useAuth } from '../hooks/useAuth';

const STATUS_COPY = {
  active: { label: 'Active', color: 'var(--moss)', bg: 'rgba(63,90,70,0.12)' },
  inactive: { label: 'Not subscribed', color: 'var(--muted)', bg: 'rgba(107,106,98,0.12)' },
  past_due: { label: 'Payment failed', color: 'var(--rust)', bg: 'var(--rust-bg)' },
  canceled: { label: 'Canceled', color: 'var(--rust)', bg: 'var(--rust-bg)' },
};

export default function BillingPage() {
  const { tenantId } = useAuth();
  const [status, setStatus] = useState(null);
  const [redirecting, setRedirecting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!tenantId) return;
    billingApi.status(tenantId).then(setStatus);
  }, [tenantId]);

  async function handleUpgrade() {
    setError('');
    setRedirecting(true);
    try {
      const { checkout_url } = await billingApi.createCheckoutSession(tenantId);
      window.location.href = checkout_url;
    } catch (err) {
      setError(err.status === 403 ? 'Only the workspace owner can manage billing.' : 'Could not start checkout.');
      setRedirecting(false);
    }
  }

  if (!status) return <p style={{ color: 'var(--muted)' }}>Loading…</p>;
  const copy = STATUS_COPY[status.subscription_status] || STATUS_COPY.inactive;

  return (
    <div style={{ maxWidth: 480 }}>
      <h2 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 1.5rem' }}>Billing</h2>

      <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: '1.5rem' }}>
        <span style={{ fontSize: 13, padding: '4px 11px', borderRadius: 5, background: copy.bg, color: copy.color }}>
          {copy.label}
        </span>

        {status.subscription_status !== 'active' && (
          <>
            <p style={{ fontSize: 14, color: 'var(--muted)', margin: '16px 0' }}>
              Subscribe to unlock leads, the pipeline view, and everything your team needs day to day.
            </p>
            <button className="btn-primary" onClick={handleUpgrade} disabled={redirecting}>
              {redirecting ? 'Redirecting…' : 'Subscribe'}
            </button>
            {error && <p className="error-text">{error}</p>}
          </>
        )}
      </div>
    </div>
  );
}
