import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { portalApi } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { usePortal } from '@/store/portal';
import { formatKes } from '@/utils/money';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Filter from '@/components/ui/Filter';

export default function PortalCatalog() {
  const [search, setSearch] = useState('');
  const addToCart = usePortal((s) => s.addToCart);
  const cart = usePortal((s) => s.cart);

  const { data, isLoading } = useQuery({
    queryKey: ['portal-catalog', search],
    queryFn: async () => (await portalApi.get(endpoints.preorders.portal.catalog, {
      params: { search: search || undefined, page_size: 60 },
    })).data,
  });

  const products = data?.results || data || [];
  const cartCount = cart.reduce((sum, c) => sum + c.quantity, 0);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="font-bold text-lg text-brand-700">DEMKA</h1>
          <a href="/portal/cart" className="relative btn-primary btn-sm">
            Cart {cartCount > 0 && <span className="ml-1">({cartCount})</span>}
          </a>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-4">
        <Filter title="Catalog filters" activeCount={search ? 1 : 0} onClear={() => setSearch('')} showClear>
          <Input
            placeholder="Search parts by name, SKU, or compatibility..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </Filter>

        {isLoading ? (
          <div>Loading...</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {products.map((p) => (
              <div key={p.id} className="card flex flex-col">
                <div className="flex-1">
                  {p.image ? (
                    <img src={p.image} alt="" className="mb-3 aspect-[16/9] w-full rounded object-cover" />
                  ) : (
                    <div className="mb-3 flex aspect-[16/9] w-full items-center justify-center rounded bg-slate-100 text-xs text-slate-400">
                      No image
                    </div>
                  )}
                  <div className="font-semibold">{p.name}</div>
                  <div className="text-xs text-slate-500 mb-1">
                    SKU: {p.sku}{p.part_number && ` · Part No: ${p.part_number}`}{p.brand && ` · ${p.brand}`}
                  </div>
                  {p.compatibility_notes && (
                    <div className="text-xs text-slate-500 mb-2 line-clamp-2">
                      {p.compatibility_notes}
                    </div>
                  )}
                  <div className="text-lg font-semibold text-brand-700">
                    {formatKes(p.wholesale_price)}
                  </div>
                  <div className="text-xs mt-1">
                    {p.is_special_order ? (
                      <span className="badge-warning">Order on request</span>
                    ) : (
                      <span className="badge-success">In stock</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => addToCart(p, 1)}
                  className="btn-primary mt-3 w-full"
                >
                  Add to Order
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}