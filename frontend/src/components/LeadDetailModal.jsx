import { useEffect, useState, useCallback } from 'react';
import { leadApi } from '../api/resources';
import { useAuth } from '../hooks/useAuth';
import { useTenantSocket } from '../hooks/useTenantSocket';

const STATUS_OPTIONS = ['new', 'contacted', 'qualified', 'proposal_sent', 'won', 'lost'];

export default function LeadDetailModal({ leadId, onClose, onSaved }) {
  const { tenantId } = useAuth();
  const [lead, setLead] = useState(null);
  const [status, setStatus] = useState('');
  const [conflict, setConflict] = useState(false);
  const [saving, setSaving] = useState(false);
  const [viewers, setViewers] = useState([]);

  const loadLead = useCallback(async () => {
    const leads = await leadApi.list(tenantId);
    const found = leads.find((l) => l.id === leadId);
    setLead(found);
    setStatus(found?.status_code || '');
    setConflict(false);
  }, [tenantId, leadId]);

  useEffect(() => { loadLead(); }, [loadLead]);

  const handleSocketEvent = useCallback((event) => {
    if (event.type === 'presence' && event.lead_id === leadId) {
      setViewers(event.viewers);
    }
    if (event.type === 'conflict_warning' && event.lead_id === leadId) {
      setConflict(true);
    }
    if (event.type === 'lead_changed' && event.lead_id === leadId) {
      // Someone else's change landed — don't clobber an in-progress edit,
      // just flag it. The person decides when to reload.
      setConflict(true);
    }
  }, [leadId]);

  const { send } = useTenantSocket(tenantId, handleSocketEvent);

  // Announce presence on open, retract on close — this is what lets
  // teammates see "someone's viewing this lead" in real time.
  useEffect(() => {
    send({ type: 'view_lead', lead_id: leadId });
    return () => send({ type: 'leave_lead', lead_id: leadId });
  }, [leadId, send]);

  async function handleSave() {
    setSaving(true);
    try {
      await leadApi.update(tenantId, leadId, { version: lead.version, status_code: status });
      await onSaved?.();
      onClose();
    } catch (err) {
      if (err.status === 409) {
        setConflict(true);
      }
    } finally {
      setSaving(false);
    }
  }

  if (!lead) return null;

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(28,35,31,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
      <div style={{ background: 'var(--card)', borderRadius: 10, padding: '1.75rem', width: '100%', maxWidth: 440 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{lead.name}</h3>
            <p style={{ margin: '2px 0 0', fontSize: 13, color: 'var(--muted)' }}>{lead.company || 'No company'}</p>
          </div>
          <button onClick={onClose} className="btn-secondary" style={{ height: 32, padding: '0 10px' }}>Close</button>
        </div>

        {viewers.length > 1 && (
          <p style={{ fontSize: 12.5, color: 'var(--moss)', marginTop: 10 }}>
            {viewers.length} people viewing this lead right now
          </p>
        )}

        {conflict && (
          <div style={{ background: 'var(--rust-bg)', color: 'var(--rust)', borderRadius: 6, padding: '10px 12px', fontSize: 13, marginTop: 12 }}>
            This lead changed since you opened it.{' '}
            <button onClick={loadLead} style={{ background: 'none', border: 'none', color: 'var(--rust)', fontWeight: 600, textDecoration: 'underline', padding: 0 }}>
              Reload
            </button>{' '}
            before saving.
          </div>
        )}

        <div className="field" style={{ marginTop: 16 }}>
          <label htmlFor="status">Stage</label>
          <select id="status" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>
        </div>

        <button className="btn-primary" style={{ width: '100%' }} onClick={handleSave} disabled={saving || conflict}>
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </div>
  );
}
