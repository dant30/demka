import { useEffect } from 'react';
import { useAuth as useAuthStore } from '@/store/auth';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { storage } from '@/storage/localStorage';

export function useAuth() {
  const { user, setUser, setAuth, logout } = useAuthStore();

  useEffect(() => {
    // Revalidate the token on mount
    if (!user && storage.getItem('access_token')) {
      api.get(endpoints.auth.me)
        .then(({ data }) => setUser(data))
        .catch(() => logout());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (identifier, password) => {
    const { data } = await api.post(endpoints.auth.login, { identifier, password });
    setAuth({ user: data.user, access: data.access, refresh: data.refresh });
    return data;
  };

  const logoutUser = async () => {
    const refresh = storage.getItem('refresh_token');
    try {
      if (refresh) await api.post(endpoints.auth.logout, { refresh });
    } catch {
      // Ignore — token may already be blacklisted
    }
    logout();
  };

  return {
    user,
    isAuthenticated: !!user,
    isBoss: user && (user.role === 'BOSS' || user.role === 'ADMIN'),
    isFieldAgent: user?.role === 'FIELD_AGENT',
    isSalesHelper: user?.role === 'SALES_HELPER',
    login,
    logout: logoutUser,
  };
}