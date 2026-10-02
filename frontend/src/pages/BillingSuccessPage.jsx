import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { billingApi } from '../api/resources';
import { useAuth } from '../hooks/useAuth';

export default function BillingSuccessPage() {
  const { tenantId } = useAuth();
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    // The webhook may take a moment to arrive and process — poll briefly.
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      const data = await billingApi.status(tenantId);
      if (data.subscription_status === 'active' || attempts > 10) {
        setStatus(data.subscription_status === 'active' ? 'active' : 'pending');
        clearInterval(interval);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [tenantId]);

  return (
    <div style={{ padding: '2rem' }}>
      {status === 'checking' && <p>Confirming your subscription…</p>}
      {status === 'active' && (
        <>
          <h2 style={{ color: 'var(--moss)' }}>You're subscribed 🎉</h2>
          <p><Link to="/">Go to your dashboard</Link></p>
        </>
      )}
      {status === 'pending' && (
        <>
          <p>Payment received — still waiting on confirmation. Refresh in a moment.</p>
          <p><Link to="/billing">Back to billing</Link></p>
        </>
      )}
    </div>
  );
}