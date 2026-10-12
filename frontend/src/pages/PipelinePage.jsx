import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { leadApi } from '../api/resources';
import { useAuth } from '../hooks/useAuth';
import { useTenantSocket } from '../hooks/useTenantSocket';

const STAGE_LABELS = {
  new: 'New', contacted: 'Contacted', qualified: 'Qualified',
  proposal_sent: 'Proposal', won: 'Won', lost: 'Lost',
};

export default function PipelinePage() {
  const { tenantId } = useAuth();
  const [summary, setSummary] = useState(null);
  const [forbidden, setForbidden] = useState(false);
  const [notSubscribed, setNotSubscribed] = useState(false);

  const load = useCallback(async () => {
    if (!tenantId) return;
    try {
      const data = await leadApi.pipelineSummary(tenantId);
      setSummary(data);
    } catch (err) {
      if (err.status === 403) setForbidden(true);
      if (err.status === 402) setNotSubscribed(true);
    }
  }, [tenantId]);

  useEffect(() => { load(); }, [load]);

  const handleSocketEvent = useCallback((event) => {
    if (event.type === 'pipeline_updated' || event.type === 'lead_changed') load();
  }, [load]);

  useTenantSocket(tenantId, handleSocketEvent);

  if (forbidden) {
    return <p style={{ color: 'var(--muted)' }}>Pipeline view is available to admins and owners.</p>;
  }
  if (notSubscribed) {
    return (
      <div>
        <p style={{ color: 'var(--muted)', marginBottom: 12 }}>This workspace isn't subscribed yet.</p>
        <Link to="/billing" className="btn-primary" style={{ display: 'inline-block', textDecoration: 'none' }}>
          Go to billing
        </Link>
      </div>
    );
  }
  if (!summary) return <p style={{ color: 'var(--muted)' }}>Loading…</p>;

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 600, margin: '0 0 1.5rem' }}>Team pipeline</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: 12, marginBottom: 24 }}>
        <StatCard label="Total leads" value={summary.total} />
        <StatCard label="Won" value={summary.won} />
        <StatCard label="Lost" value={summary.lost} />
        <StatCard label="Conversion" value={`${summary.conversion_rate}%`} />
      </div>

      <p style={{ fontSize: 13, color: 'var(--muted)', margin: '0 0 8px' }}>Leads by stage</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, minmax(0,1fr))', gap: 10 }}>
        {Object.entries(STAGE_LABELS).map(([code, label]) => (
          <div key={code} style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: 10, textAlign: 'center' }}>
            <p style={{ fontSize: 12, color: 'var(--muted)', margin: 0 }}>{label}</p>
            <p style={{ fontSize: 18, fontWeight: 500, margin: '4px 0 0' }}>{summary.by_status[code] || 0}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: '1rem' }}>
      <p style={{ fontSize: 13, color: 'var(--muted)', margin: 0 }}>{label}</p>
      <p style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 500, margin: '4px 0 0' }}>{value}</p>
    </div>
  );
}
