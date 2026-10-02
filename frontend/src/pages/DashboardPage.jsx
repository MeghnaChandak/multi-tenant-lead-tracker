import { useEffect, useState, useCallback } from 'react';
import { leadApi } from '../api/resources';
import { useAuth } from '../hooks/useAuth';
import { useTenantSocket } from '../hooks/useTenantSocket';
import LeadDetailModal from '../components/LeadDetailModal';

export default function DashboardPage() {
  const { tenantId } = useAuth();
  const [dueToday, setDueToday] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeadId, setSelectedLeadId] = useState(null);

  const loadDueToday = useCallback(async () => {
    if (!tenantId) return;
    const leads = await leadApi.dueToday(tenantId);
    setDueToday(leads);
    setLoading(false);
  }, [tenantId]);

  useEffect(() => { loadDueToday(); }, [loadDueToday]);

  const handleSocketEvent = useCallback((event) => {
    // Any lead change could affect who's due today — simplest correct
    // approach for this scale is to refetch rather than hand-patch state.
    if (event.type === 'lead_changed' || event.type === 'pipeline_updated') {
      loadDueToday();
    }
  }, [loadDueToday]);

  useTenantSocket(tenantId, handleSocketEvent);

  if (loading) return <p style={{ color: 'var(--muted)' }}>Loading…</p>;

  return (
    <div>
      <div style={{ marginBottom: '1.75rem' }}>
        <h2 style={{ fontSize: 20, fontWeight: 600, margin: 0 }}>Good morning</h2>
        <p style={{ fontSize: 13, color: 'var(--muted)', margin: '4px 0 0' }}>
          {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
        </p>
      </div>

      <div style={{ background: 'var(--ink)', borderRadius: 10, padding: '1.75rem 2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h3 style={{ color: '#F1F0EB', fontSize: 16, fontWeight: 500, margin: 0 }}>Needs follow-up today</h3>
          <span style={{ color: 'var(--rust)', background: 'rgba(193,84,44,0.18)', fontSize: 13, padding: '3px 10px', borderRadius: 5 }}>
            {dueToday.length} lead{dueToday.length !== 1 ? 's' : ''}
          </span>
        </div>

        {dueToday.length === 0 ? (
          <p style={{ color: '#9A9C96', fontSize: 14 }}>Nothing needs attention today. Nice.</p>
        ) : (
          <div>
            {dueToday.map((lead) => (
              <div
                key={lead.id}
                onClick={() => setSelectedLeadId(lead.id)}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 4px', borderBottom: '1px solid rgba(255,255,255,0.08)', cursor: 'pointer' }}
              >
                <div>
                  <p style={{ color: '#F1F0EB', fontSize: 14.5, fontWeight: 500, margin: 0 }}>{lead.name}</p>
                  <p style={{ color: '#9A9C96', fontSize: 12.5, margin: '2px 0 0' }}>{lead.company || 'No company'}</p>
                </div>
                <span className={`stage-pill stage-${lead.status_code}`}>{lead.status_code.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedLeadId && (
        <LeadDetailModal
          leadId={selectedLeadId}
          onClose={() => setSelectedLeadId(null)}
          onSaved={loadDueToday}
        />
      )}
    </div>
  );
}
