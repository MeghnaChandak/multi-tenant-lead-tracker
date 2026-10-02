import { Link } from 'react-router-dom';

export default function BillingCancelledPage() {
  return (
    <div style={{ padding: '2rem' }}>
      <h2>Checkout cancelled</h2>
      <p><Link to="/billing">Back to billing</Link></p>
    </div>
  );
}