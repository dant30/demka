import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';

function ProductSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
      {Array.from({ length: 10 }).map((_, index) => (
        <div
          key={index}
          className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="aspect-[4/3] animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
          <div className="mt-3 h-4 w-3/4 animate-pulse rounded bg-slate-100 dark:bg-slate-800" />
          <div className="mt-2 h-3 w-1/2 animate-pulse rounded bg-slate-100 dark:bg-slate-800" />
          <div className="mt-4 h-5 w-2/3 animate-pulse rounded bg-slate-100 dark:bg-slate-800" />
          <div className="mt-3 h-8 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
        </div>
      ))}
    </div>
  );
}

function EmptyProducts() {
  return (
    <div className="flex min-h-[280px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 px-6 py-12 text-center dark:border-slate-700 dark:bg-slate-900/40">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-slate-800">
        <svg
          className="h-7 w-7"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          aria-hidden="true"
        >
          <path d="M3 7h18l-2 13H5L3 7Z" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M8 7a4 4 0 0 1 8 0" strokeLinecap="round" />
        </svg>
      </div>

      <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
        No products found
      </h3>

      <p className="mt-1 max-w-xs text-sm text-slate-500 dark:text-slate-400">
        Try changing your search or selecting another category.
      </p>
    </div>
  );
}

function StockBadge({ quantity }) {
  const stock = Number(quantity) || 0;

  const status =
    stock <= 0
      ? {
          label: 'Out of stock',
          classes: 'bg-red-50 text-red-700 ring-red-600/10 dark:bg-red-500/10 dark:text-red-400',
          dot: 'bg-red-500',
        }
      : stock <= 5
        ? {
            label: 'Low stock',
            classes: 'bg-amber-50 text-amber-700 ring-amber-600/10 dark:bg-amber-500/10 dark:text-amber-400',
            dot: 'bg-amber-500',
          }
        : {
            label: `${stock.toFixed(0)} in stock`,
            classes: 'bg-emerald-50 text-emerald-700 ring-emerald-600/10 dark:bg-emerald-500/10 dark:text-emerald-400',
            dot: 'bg-emerald-500',
          };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-[10px] font-semibold ring-1 ring-inset ${status.classes}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
      {status.label}
    </span>
  );
}

function ProductCard({ product, onAdd }) {
  const quantity = Number(product.total_quantity) || 0;
  const unavailable = quantity <= 0;

  return (
    <button
      type="button"
      onClick={() => onAdd(product)}
      disabled={unavailable}
      aria-label={`Add ${product.name} to order, ${formatKes(product.retail_price)}`}
      className="group relative flex min-w-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-400 hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-brand-500 dark:focus-visible:ring-offset-slate-950"
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-slate-100 dark:bg-slate-800">
        {product.image ? (
          <img
            src={product.image}
            alt={product.name}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-slate-400 dark:text-slate-500">
            <svg
              className="h-9 w-9"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.4"
              aria-hidden="true"
            >
              <rect x="3" y="3" width="18" height="18" rx="3" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="m21 15-5-5L5 21" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-[10px] font-medium">No image</span>
          </div>
        )}

        <div className="absolute left-2 top-2">
          <StockBadge quantity={quantity} />
        </div>

        {unavailable && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/40">
            <span className="rounded-lg bg-white/95 px-3 py-1.5 text-xs font-bold text-red-600 shadow">
              Unavailable
            </span>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col p-3 sm:p-3.5">
        <div className="min-w-0 flex-1">
          <h3 className="line-clamp-2 min-h-9 text-xs font-semibold leading-4 text-slate-900 dark:text-slate-100 sm:text-sm">
            {product.name}
          </h3>

          <div className="mt-1.5 flex min-w-0 flex-wrap items-center gap-x-1.5 gap-y-1 text-[10px] text-slate-500 dark:text-slate-400">
            {product.sku && (
              <span className="truncate font-medium">{product.sku}</span>
            )}

            {product.part_number && (
              <>
                {product.sku && <span aria-hidden="true">·</span>}
                <span className="truncate">{product.part_number}</span>
              </>
            )}
          </div>
        </div>

        <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-bold tracking-tight text-brand-700 dark:text-brand-400 sm:text-base">
              {formatKes(product.retail_price)}
            </span>

            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors ${unavailable ? 'bg-slate-100 text-slate-400 dark:bg-slate-800' : 'bg-brand-50 text-brand-700 group-hover:bg-brand-600 group-hover:text-white dark:bg-brand-500/10 dark:text-brand-400'}`}
              aria-hidden="true"
            >
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 5v14M5 12h14" />
              </svg>
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}

export default function ProductGrid({ onAdd, search, categoryId }) {
  const { data, isLoading, isError, refetch } = useList(
    'products',
    endpoints.inventory.products,
    {
      search: search || undefined,
      category: categoryId || undefined,
      page_size: 60,
    }
  );

  const products = Array.isArray(data?.results)
    ? data.results
    : Array.isArray(data)
      ? data
      : [];

  if (isLoading) {
    return <ProductSkeleton />;
  }

  if (isError) {
    return (
      <div className="flex min-h-[240px] flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50/50 p-6 text-center dark:border-red-900/50 dark:bg-red-950/20">
        <p className="text-sm font-semibold text-red-700 dark:text-red-400">
          Couldn't load products
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Check your connection and try again.
        </p>
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-red-700"
        >
          Try again
        </button>
      </div>
    );
  }

  if (products.length === 0) {
    return <EmptyProducts />;
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onAdd={onAdd}
        />
      ))}
    </div>
  );
}
