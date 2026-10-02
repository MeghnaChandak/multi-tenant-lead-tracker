import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function RequireAuth({ children }) {
  const { isAuthed, tenantId } = useAuth();
  if (!isAuthed) return <Navigate to="/login" replace />;
  if (!tenantId) return <Navigate to="/register" replace />;
  return children;
}
