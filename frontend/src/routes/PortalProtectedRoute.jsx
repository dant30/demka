import { Navigate } from 'react-router-dom';
import { usePortal } from '@/store/portal';

export default function PortalProtectedRoute({ children }) {
  const token = usePortal((s) => s.token);
  if (!token) return <Navigate to="/portal/login" replace />;
  return children;
}