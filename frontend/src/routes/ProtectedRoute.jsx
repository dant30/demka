import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export default function ProtectedRoute({ children, bossOnly = false, shopOnly = false }) {
  const { isAuthenticated, isBoss, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (shopOnly && user?.role === 'FIELD_AGENT') {
    return <Navigate to="/field" replace />;
  }
  if (bossOnly && !isBoss) {
    return <Navigate to={user?.role === 'FIELD_AGENT' ? '/field' : '/pos'} replace />;
  }
  return children;
}