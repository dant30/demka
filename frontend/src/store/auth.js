import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { storage } from '@/storage/localStorage';

export const useAuth = create(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setAuth: ({ user, access, refresh }) => {
        if (access) storage.setItem('access_token', access);
        if (refresh) storage.setItem('refresh_token', refresh);
        set({ user, accessToken: access, refreshToken: refresh });
      },

      setUser: (user) => set({ user }),

      logout: () => {
        storage.removeItem('access_token');
        storage.removeItem('refresh_token');
        set({ user: null, accessToken: null, refreshToken: null });
      },

      isBoss: () => {
        const role = useAuth.getState().user?.role;
        return role === 'BOSS' || role === 'ADMIN';
      },
    }),
    { name: 'demka_auth', storage: createJSONStorage(() => storage) }
  )
);