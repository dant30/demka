import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export default function ProtectedRoute({ children, bossOnly = false }) {
  const { isAuthenticated, isBoss } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (bossOnly && !isBoss) {
    return <Navigate to="/pos" replace />;
  }
  return children;
}