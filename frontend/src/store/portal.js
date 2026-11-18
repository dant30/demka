import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { storage } from '@/storage/localStorage';

export const usePortal = create(
  persist(
    (set) => ({
      customer: null,
      token: null,
      cart: [],

      setAuth: ({ customer, token }) => {
        if (token) storage.setItem('portal_token', token);
        storage.setJSON('portal_customer', customer || null);
        set({ customer, token });
      },

      logout: () => {
        storage.removeItem('portal_token');
        storage.removeItem('portal_customer');
        set({ customer: null, token: null, cart: [] });
      },

      addToCart: (product, qty = 1) => {
        const cart = [...usePortal.getState().cart];
        const existing = cart.find((c) => c.product.id === product.id);
        if (existing) existing.quantity += qty;
        else cart.push({ product, quantity: qty });
        set({ cart });
      },

      updateQty: (productId, qty) => {
        const cart = usePortal.getState().cart
          .map((c) => (c.product.id === productId ? { ...c, quantity: qty } : c))
          .filter((c) => c.quantity > 0);
        set({ cart });
      },

      removeFromCart: (productId) => {
        set({ cart: usePortal.getState().cart.filter((c) => c.product.id !== productId) });
      },

      clearCart: () => set({ cart: [] }),
    }),
    { name: 'demka_portal', storage: createJSONStorage(() => storage) }
  )
);