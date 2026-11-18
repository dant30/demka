import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';

export default function ProductGrid({ onAdd, search, categoryId }) {
  const { data, isLoading } = useList(
    'products',
    endpoints.inventory.products,
    { search: search || undefined, category: categoryId || undefined, page_size: 60 }
  );
  const products = data?.results || data || [];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3 md:gap-3 lg:grid-cols-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="card animate-pulse h-28" />
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        No products match your search.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-3 md:gap-3 lg:grid-cols-4">
      {products.map((p) => (
        <button
          key={p.id}
          onClick={() => onAdd(p)}
          className="card p-2.5 text-left hover:border-brand-500 hover:shadow-md transition md:p-4"
        >
          {p.image ? (
            <img src={p.image} alt="" className="mb-2 aspect-square w-full rounded object-cover md:aspect-[4/3]" />
          ) : (
            <div className="mb-2 flex aspect-square w-full items-center justify-center rounded bg-slate-100 text-xs text-slate-400 md:aspect-[4/3]">
              No image
            </div>
          )}
          <div className="line-clamp-2 text-[13px] leading-tight font-semibold text-slate-900 md:text-sm md:truncate md:line-clamp-none">{p.name}</div>
          <div className="mb-2 text-xs text-slate-500">
            {p.sku}{p.part_number && ` · ${p.part_number}`}
          </div>
          <div className="mt-1 text-sm font-semibold text-brand-700 md:text-base">{formatKes(p.retail_price)}</div>
          <div className="text-xs text-slate-500 mt-1">
            Stock: {Number(p.total_quantity || 0).toFixed(0)}
          </div>
        </button>
      ))}
    </div>
  );
}