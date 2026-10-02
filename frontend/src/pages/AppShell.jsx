import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const navItems = [
  { to: '/', label: 'Follow-ups', end: true },
  { to: '/leads', label: 'All leads' },
  { to: '/pipeline', label: 'Pipeline' },
  { to: '/billing', label: 'Billing' },
];

export default function AppShell() {
  const { logout } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{ width: 220, flexShrink: 0, background: 'var(--card)', borderRight: '1px solid var(--line)', padding: '1.5rem 1rem', display: 'flex', flexDirection: 'column' }}>
        <p style={{ fontFamily: 'var(--font-display)', fontSize: 19, fontWeight: 500, color: 'var(--moss)', margin: '0 0 1.75rem 0.5rem' }}>
          Ledger
        </p>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            style={({ isActive }) => ({
              display: 'block',
              padding: '9px 10px',
              borderRadius: 6,
              fontSize: 14,
              marginBottom: 2,
              textDecoration: 'none',
              color: isActive ? 'var(--rust)' : 'var(--muted)',
              background: isActive ? 'var(--rust-bg)' : 'transparent',
              fontWeight: isActive ? 500 : 400,
            })}
          >
            {item.label}
          </NavLink>
        ))}
        <button
          onClick={logout}
          className="btn-secondary"
          style={{ marginTop: 'auto', fontSize: 13 }}
        >
          Sign out
        </button>
      </aside>
      <main style={{ flex: 1, padding: '2rem 2.5rem', minWidth: 0 }}>
        <Outlet />
      </main>
    </div>
  );
}
