import { create } from 'zustand';

/**
 * POS / field-sale cart.
 * Line shape: { product, quantity, unitPrice, discount, lineTotal }
 * Prices come from the product snapshot at add time; users may override.
 */
export const useCart = create((set, get) => ({
  items: [],
  customerId: null,
  locationId: null,
  channel: 'SHOP',
  saleType: 'STANDARD',
  notes: '',

  setCustomer: (customerId) => set({ customerId }),
  setLocation: (locationId) => set({ locationId }),
  setChannel: (channel) => set({ channel }),
  setSaleType: (saleType) => set({ saleType }),
  setNotes: (notes) => set({ notes }),

  addItem: (product, qty = 1) => {
    const items = [...get().items];
    const existing = items.find((i) => i.product.id === product.id);
    if (existing) {
      existing.quantity += qty;
      existing.lineTotal = (
        (existing.quantity * existing.unitPrice) - existing.discount
      );
    } else {
      const unitPrice = Number(product.wholesale_price || product.retail_price || 0);
      items.push({
        product,
        quantity: qty,
        unitPrice,
        discount: 0,
        lineTotal: unitPrice * qty,
      });
    }
    set({ items });
  },

  updateQuantity: (productId, qty) => {
    const items = get().items
      .map((i) => {
        if (i.product.id !== productId) return i;
        if (qty <= 0) return null;
        return {
          ...i,
          quantity: qty,
          lineTotal: (qty * i.unitPrice) - i.discount,
        };
      })
      .filter(Boolean);
    set({ items });
  },

  updatePrice: (productId, unitPrice) => {
    const items = get().items.map((i) =>
      i.product.id === productId
        ? { ...i, unitPrice, lineTotal: i.quantity * unitPrice - i.discount }
        : i
    );
    set({ items });
  },

  removeItem: (productId) =>
    set({ items: get().items.filter((i) => i.product.id !== productId) }),

  clear: () =>
    set({
      items: [], customerId: null, locationId: null,
      channel: 'SHOP', saleType: 'STANDARD', notes: '',
    }),

  subtotal: () => get().items.reduce((sum, i) => sum + i.lineTotal, 0),
  itemCount: () => get().items.reduce((sum, i) => sum + i.quantity, 0),
}));