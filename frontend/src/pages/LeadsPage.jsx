import { useEffect, useState, useCallback } from 'react';
import { leadApi } from '../api/resources';
import { useAuth } from '../hooks/useAuth';
import LeadDetailModal from '../components/LeadDetailModal';

export default function LeadsPage() {
  const { tenantId } = useAuth();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [form, setForm] = useState({ name: '', company: '', phone: '', email: '' });
  const [duplicates, setDuplicates] = useState([]);

  const load = useCallback(async () => {
    if (!tenantId) return;
    const data = await leadApi.list(tenantId);
    setLeads(data);
    setLoading(false);
  }, [tenantId]);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    const result = await leadApi.create(tenantId, form);
    setDuplicates(result.possible_duplicates);
    setForm({ name: '', company: '', phone: '', email: '' });
    if (result.possible_duplicates.length === 0) setShowForm(false);
    load();
  }

  if (loading) return <p style={{ color: 'var(--muted)' }}>Loading…</p>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: 20, fontWeight: 600, margin: 0 }}>All leads</h2>
        <button className="btn-primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : 'New lead'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: '1.25rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="field">
              <label>Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="field">
              <label>Company</label>
              <input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            </div>
            <div className="field">
              <label>Phone</label>
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div className="field">
              <label>Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
          </div>
          <button className="btn-primary">Add lead</button>

          {duplicates.length > 0 && (
            <div style={{ marginTop: 12, background: 'var(--rust-bg)', color: 'var(--rust)', borderRadius: 6, padding: '10px 12px', fontSize: 13 }}>
              This might already exist: {duplicates.map((d) => d.name).join(', ')} — added anyway.
            </div>
          )}
        </form>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5 }}>
        <thead>
          <tr>
            {['Name', 'Company', 'Stage', 'Next follow-up'].map((h) => (
              <th key={h} style={{ textAlign: 'left', fontWeight: 500, color: 'var(--muted)', fontSize: 12.5, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id} onClick={() => setSelectedLeadId(lead.id)} style={{ cursor: 'pointer' }}>
              <td style={{ padding: '11px 0', borderBottom: '1px solid var(--line)', fontWeight: 500 }}>{lead.name}</td>
              <td style={{ padding: '11px 0', borderBottom: '1px solid var(--line)', color: 'var(--muted)' }}>{lead.company || '—'}</td>
              <td style={{ padding: '11px 0', borderBottom: '1px solid var(--line)' }}>
                <span className={`stage-pill stage-${lead.status_code}`}>{lead.status_code.replace('_', ' ')}</span>
              </td>
              <td style={{ padding: '11px 0', borderBottom: '1px solid var(--line)', color: 'var(--muted)' }}>
                {lead.next_follow_up_date || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedLeadId && (
        <LeadDetailModal leadId={selectedLeadId} onClose={() => setSelectedLeadId(null)} onSaved={load} />
      )}
    </div>
  );
}
