import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { isBossRole, landingPathFor } from '@/utils/roles';
import Dashboard from '@/pages/Dashboard';

export default function HomeRoute() {
  const { user } = useAuth();

  if (!user) return null;
  if (isBossRole(user.role)) return <Dashboard />;
  return <Navigate to={landingPathFor(user.role)} replace />;
}
