import axios from 'axios';
import { storage } from '@/storage/localStorage';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ---- Request interceptor: attach JWT ----
api.interceptors.request.use((config) => {
  const token = storage.getItem('access_token');
  if (token && !config.skipAuth) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- Response interceptor: unwrap, refresh on 401 ----
let refreshing = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;

    // Attempt one refresh on 401 (not on the refresh endpoint itself)
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/accounts/auth/refresh/') &&
      !original.url?.includes('/accounts/auth/login/') &&
      !original.url?.includes('/preorders/portal/auth/')
    ) {
      original._retry = true;
      try {
        refreshing = refreshing || doRefresh();
        const newAccess = await refreshing;
        refreshing = null;
        if (newAccess) {
          original.headers.Authorization = `Bearer ${newAccess}`;
          return api(original);
        }
      } catch {
        refreshing = null;
      }
      // Refresh failed — clean logout
      storage.removeItem('access_token');
      storage.removeItem('refresh_token');
      storage.removeItem('demka_auth');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

async function doRefresh() {
  const refresh = storage.getItem('refresh_token');
  if (!refresh) throw new Error('no refresh token');
  const { data } = await axios.post(
    `${API_URL}/accounts/auth/refresh/`,
    { refresh },
    { headers: { 'Content-Type': 'application/json' } }
  );
  storage.setItem('access_token', data.access);
  return data.access;
}

// ---- Portal client (separate token storage for customer portal) ----
export const portalApi = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

portalApi.interceptors.request.use((config) => {
  const token = storage.getItem('portal_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

portalApi.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      storage.removeItem('portal_token');
      storage.removeItem('portal_customer');
      if (!window.location.pathname.startsWith('/portal/login')) {
        window.location.href = '/portal/login';
      }
    }
    return Promise.reject(error);
  }
);

export function extractError(err, fallback = 'Something went wrong.') {
  const body = err?.response?.data;
  if (!body) return fallback;
  const msg = body?.error?.message ?? body?.detail ?? body;
  if (typeof msg === 'string') return msg;
  if (typeof msg === 'object') {
    return Object.entries(msg)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join(' | ');
  }
  return fallback;
}