import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { useDetail, useList, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { useAuth } from '@/hooks/useAuth';
import { formatKes, formatNumber } from '@/utils/money';

import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';

function formatDate(value) {
  if (!value) return 'Not available';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? 'Not available'
    : new Intl.DateTimeFormat('en-KE', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function getErrorMessage(error) {
  return error?.response?.data?.error?.message
    || error?.response?.data?.detail
    || error?.response?.data?.message
    || 'Something went wrong. Please try again.';
}

function getProductsStock(locations = []) {
  return locations.reduce((total, location) => total + (Number(location.quantity) || 0), 0);
}

function getStockStatus(quantity, reorderLevel = 0) {
  const stock = Number(quantity) || 0;
  const reorder = Number(reorderLevel) || 0;

  if (stock <= 0) {
    return { label: 'Out of stock', dot: 'bg-red-500', classes: 'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-500/10 dark:text-red-400' };
  }
  if (stock <= reorder) {
    return { label: 'Low stock', dot: 'bg-amber-500', classes: 'bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400' };
  }
  return { label: 'In stock', dot: 'bg-emerald-500', classes: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400' };
}

function StatusBadge({ quantity, reorderLevel }) {
  const status = getStockStatus(quantity, reorderLevel);
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${status.classes}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
      {status.label}
    </span>
  );
}

function MetricCard({ label, value, description, accent = 'slate' }) {
  const accents = {
    slate: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
    brand: 'bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-400',
    emerald: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400',
    amber: 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400',
  };
  const mark = accent === 'brand' ? '↗' : accent === 'emerald' ? '✓' : accent === 'amber' ? '!' : '•';

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400 sm:text-sm">{label}</p>
          <p className="mt-2 break-words text-lg font-bold tracking-tight text-slate-900 dark:text-white sm:text-xl">{value}</p>
          {description && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{description}</p>}
        </div>
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${accents[accent] || accents.slate}`}>
          <span className="text-sm font-bold" aria-hidden="true">{mark}</span>
        </div>
      </div>
    </div>
  );
}

function SectionHeader({ title, description, action }) {
  return (
    <div className="flex flex-col gap-3 border-b border-slate-100 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5 dark:border-slate-800">
      <div>
        <h2 className="text-sm font-bold text-slate-900 dark:text-white sm:text-base">{title}</h2>
        {description && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{description}</p>}
      </div>
      {action}
    </div>
  );
}

function EmptyState({ title, description }) {
  return (
    <div className="flex flex-col items-center justify-center px-5 py-10 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500">
        <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
          <path d="M3 7h18l-2 13H5L3 7Z" /><path d="M8 7a4 4 0 0 1 8 0" />
        </svg>
      </div>
      <h3 className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">{title}</h3>
      <p className="mt-1 max-w-sm text-xs leading-5 text-slate-500 dark:text-slate-400">{description}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="mx-auto max-w-6xl space-y-5 animate-pulse">
      <div className="h-8 w-48 rounded-lg bg-slate-200 dark:bg-slate-800" />
      <div className="h-40 rounded-2xl bg-slate-200 dark:bg-slate-800" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[1, 2, 3, 4].map((item) => <div key={item} className="h-28 rounded-2xl bg-slate-200 dark:bg-slate-800" />)}
      </div>
      <div className="h-64 rounded-2xl bg-slate-200 dark:bg-slate-800" />
    </div>
  );
}

function StockLocations({ locations, isBoss, onAdjust }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <SectionHeader
        title="Stock by location"
        description="View inventory quantities across your branches and stores."
        action={isBoss ? <Button size="sm" onClick={() => onAdjust(null)}>+ Adjust stock</Button> : null}
      />

      {locations.length === 0 ? (
        <EmptyState title="No stock records" description="There are currently no stock records for this product." />
      ) : (
        <>
          <div className="divide-y divide-slate-100 dark:divide-slate-800 sm:hidden">
            {locations.map((location) => (
              <div key={location.location_id} className="space-y-3 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="break-words text-sm font-semibold text-slate-900 dark:text-white">{location.location_name}</p>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Reorder at {formatNumber(location.reorder_level || 0, 0)}</p>
                  </div>
                  <StatusBadge quantity={location.quantity} reorderLevel={location.reorder_level} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Available quantity</p>
                    <p className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{formatNumber(location.quantity, 0)}</p>
                  </div>
                  {isBoss && (
                    <button type="button" onClick={() => onAdjust(location.location_id)} className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-brand-700 transition hover:bg-brand-50 dark:border-slate-700 dark:text-brand-400 dark:hover:bg-brand-500/10">Adjust</button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="hidden overflow-x-auto sm:block">
            <table className="w-full min-w-[600px] text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
                <tr><th className="px-5 py-3">Location</th><th className="px-5 py-3 text-right">Quantity</th><th className="px-5 py-3 text-right">Reorder at</th><th className="px-5 py-3">Status</th>{isBoss && <th className="px-5 py-3 text-right">Action</th>}</tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {locations.map((location) => (
                  <tr key={location.location_id} className="transition hover:bg-slate-50/70 dark:hover:bg-slate-800/30">
                    <td className="px-5 py-4 font-semibold text-slate-900 dark:text-slate-100">{location.location_name}</td>
                    <td className="px-5 py-4 text-right font-bold tabular-nums text-slate-900 dark:text-white">{formatNumber(location.quantity, 0)}</td>
                    <td className="px-5 py-4 text-right text-slate-500 dark:text-slate-400">{formatNumber(location.reorder_level || 0, 0)}</td>
                    <td className="px-5 py-4"><StatusBadge quantity={location.quantity} reorderLevel={location.reorder_level} /></td>
                    {isBoss && <td className="px-5 py-4 text-right"><button type="button" onClick={() => onAdjust(location.location_id)} className="text-xs font-semibold text-brand-600 hover:text-brand-800 hover:underline dark:text-brand-400">Adjust stock</button></td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

function MovementHistory({ movements }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <SectionHeader title="Recent stock movements" description={movements.length ? `${movements.length} recent transaction${movements.length === 1 ? '' : 's'}` : 'Track stock additions, removals and adjustments.'} />
      {movements.length === 0 ? (
        <EmptyState title="No movements yet" description="Stock transactions will appear here when inventory changes." />
      ) : (
        <>
          <div className="divide-y divide-slate-100 dark:divide-slate-800 sm:hidden">
            {movements.map((movement) => {
              const quantity = Number(movement.quantity) || 0;
              const positive = quantity >= 0;
              return (
                <div key={movement.id} className="space-y-2.5 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0"><p className="text-sm font-semibold text-slate-900 dark:text-white">{movement.movement_type_display || 'Stock movement'}</p><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{formatDate(movement.created_at)}</p></div>
                    <span className={`shrink-0 text-sm font-bold tabular-nums ${positive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>{positive ? '+' : ''}{formatNumber(quantity, 0)}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400"><span>{movement.location_name || 'Unknown location'}</span><span>{movement.reference_type || 'No reference'}{movement.reference_id ? ` #${movement.reference_id}` : ''}</span></div>
                </div>
              );
            })}
          </div>

          <div className="hidden overflow-x-auto sm:block">
            <table className="w-full min-w-[700px] text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-800/60 dark:text-slate-400"><tr><th className="px-5 py-3">Date</th><th className="px-5 py-3">Movement</th><th className="px-5 py-3">Location</th><th className="px-5 py-3 text-right">Quantity</th><th className="px-5 py-3">Reference</th></tr></thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {movements.map((movement) => {
                  const quantity = Number(movement.quantity) || 0;
                  const positive = quantity >= 0;
                  return (
                    <tr key={movement.id} className="transition hover:bg-slate-50/70 dark:hover:bg-slate-800/30">
                      <td className="whitespace-nowrap px-5 py-4 text-xs text-slate-500 dark:text-slate-400">{formatDate(movement.created_at)}</td>
                      <td className="px-5 py-4 font-medium text-slate-900 dark:text-slate-100">{movement.movement_type_display || 'Stock movement'}</td>
                      <td className="px-5 py-4 text-slate-600 dark:text-slate-400">{movement.location_name || '—'}</td>
                      <td className={`px-5 py-4 text-right font-bold tabular-nums ${positive ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>{positive ? '+' : ''}{formatNumber(quantity, 0)}</td>
                      <td className="px-5 py-4 text-xs text-slate-500 dark:text-slate-400">{movement.reference_type || '—'}{movement.reference_id ? ` #${movement.reference_id}` : ''}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isBoss } = useAuth();

  const { data: product, isLoading, isError, refetch: refetchProduct } = useDetail('product', endpoints.inventory.productDetail(id), id);
  const { data: summary, refetch: refetchSummary } = useDetail('product-summary', endpoints.inventory.productSummary(id), id);
  const { data: movementData } = useList('product-movements', endpoints.inventory.movements, { product: id, page_size: 20 });

  const [showAdjust, setShowAdjust] = useState(false);
  const [adjustLoc, setAdjustLoc] = useState(null);

  const locations = summary?.by_location || product?.stock_by_location || [];
  const movements = Array.isArray(movementData?.results) ? movementData.results : Array.isArray(movementData) ? movementData : [];

  const hasTotalStock = product?.total_quantity !== null && product?.total_quantity !== undefined && Number.isFinite(Number(product.total_quantity));
  const totalStock = hasTotalStock ? Number(product.total_quantity) : getProductsStock(locations);
  const reorderLevel = Number(product?.reorder_level) || 0;
  const stockStatus = getStockStatus(totalStock, reorderLevel);
  const hasCostPrice = product?.cost_price !== null && product?.cost_price !== undefined;

  const handleAdjust = (locationId = null) => {
    setAdjustLoc(locationId);
    setShowAdjust(true);
  };

  const refreshInventory = () => {
    refetchProduct();
    refetchSummary();
  };

  if (isLoading) return <LoadingState />;

  if (!product) {
    return (
      <div className="mx-auto max-w-5xl rounded-2xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-900/50 dark:bg-red-950/20">
        <h2 className="text-base font-bold text-red-700 dark:text-red-400">Unable to load product</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">The product could not be found or its details could not be retrieved.</p>
        <div className="mt-4 flex justify-center gap-2"><Button variant="secondary" onClick={() => navigate(-1)}>Go back</Button><Button onClick={() => refetchProduct()}>Try again</Button></div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl space-y-5 pb-8">
      {isError && (
        <div role="status" className="flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300">
          <span>Some live details could not be refreshed. Showing cached product information.</span>
          <button type="button" onClick={() => refetchProduct()} className="shrink-0 font-bold underline underline-offset-4">Try again</button>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <button type="button" onClick={() => navigate(-1)} className="inline-flex items-center gap-2 rounded-lg py-2 text-sm font-medium text-slate-500 transition hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400"><span aria-hidden="true">←</span>Back to products</button>
        {isBoss && <Button variant="secondary" onClick={() => navigate(`/inventory/products/${id}/edit`)}>Edit product</Button>}
      </div>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:p-6">
          <div className="h-28 w-full shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800 sm:h-28 sm:w-28">
            {product.image ? <img src={product.image} alt={product.name} className="h-full w-full object-cover" /> : <div className="flex h-full flex-col items-center justify-center gap-2 text-slate-400"><span className="text-3xl" aria-hidden="true">▧</span><span className="text-xs font-medium">No image</span></div>}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2"><StatusBadge quantity={totalStock} reorderLevel={reorderLevel} />{product.brand && <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">{product.brand}</span>}</div>
            <h1 className="mt-3 break-words text-xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-2xl">{product.name}</h1>
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
              {product.sku && <span>SKU: <strong className="font-semibold text-slate-700 dark:text-slate-300">{product.sku}</strong></span>}
              {product.part_number && <span>Part No: <strong className="font-semibold text-slate-700 dark:text-slate-300">{product.part_number}</strong></span>}
            </div>
          </div>
          {isBoss && <div className="hidden shrink-0 sm:block"><Button onClick={() => handleAdjust(null)}>+ Adjust stock</Button></div>}
        </div>
        {isBoss && <div className="border-t border-slate-100 p-4 sm:hidden dark:border-slate-800"><Button className="w-full" onClick={() => handleAdjust(null)}>+ Adjust stock</Button></div>}
      </section>

      <div>
        <div className="mb-3"><h2 className="text-sm font-bold text-slate-900 dark:text-white">Product overview</h2><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Pricing and inventory summary</p></div>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <MetricCard label="Total stock" value={formatNumber(totalStock, 0)} description="Units across locations" accent="brand" />
          <MetricCard label="Cost price" value={hasCostPrice ? formatKes(product.cost_price) : 'Hidden'} description="Purchase cost per unit" />
          <MetricCard label="Retail price" value={formatKes(product.retail_price)} description="Standard selling price" accent="emerald" />
          <MetricCard label="Wholesale price" value={formatKes(product.wholesale_price)} description="Wholesale selling price" />
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <MetricCard label="Reorder level" value={formatNumber(reorderLevel, 0)} description="Minimum stock threshold" accent="amber" />
          <MetricCard label="Stock availability" value={stockStatus.label} description="Based on total stock and reorder level" accent={totalStock <= 0 ? 'slate' : totalStock <= reorderLevel ? 'amber' : 'emerald'} />
        </div>
      </div>

      <StockLocations locations={locations} isBoss={isBoss} onAdjust={handleAdjust} />
      <MovementHistory movements={movements} />

      {isBoss && <StockAdjustModal open={showAdjust} onClose={() => setShowAdjust(false)} product={product} defaultLocation={adjustLoc} onSuccess={refreshInventory} />}
    </div>
  );
}

function StockAdjustModal({ open, onClose, product, defaultLocation, onSuccess }) {
  const [location, setLocation] = useState('');
  const [delta, setDelta] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');

  const adjust = useAction('adjust', () => endpoints.inventory.stockAdjust, { invalidate: ['product', 'product-summary', 'stock-levels', 'product-movements'] });
  const { data: locations } = useList('locations', endpoints.inventory.locations);
  const availableLocations = Array.isArray(locations?.results) ? locations.results : Array.isArray(locations) ? locations : [];
  const quantity = Number(delta);
  const validAdjustment = location !== '' && delta.trim() !== '' && Number.isFinite(quantity) && quantity !== 0;
  const isRemoval = quantity < 0;

  useEffect(() => {
    if (open) {
      setLocation(defaultLocation ? String(defaultLocation) : '');
      setDelta('');
      setNotes('');
      setError('');
    }
  }, [open, defaultLocation]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    if (!location) return setError('Please select a stock location.');
    if (delta.trim() === '' || !Number.isFinite(quantity)) return setError('Please enter a valid adjustment quantity.');
    if (quantity === 0) return setError('Adjustment quantity cannot be zero.');

    try {
      await adjust.mutateAsync({ id: null, product: product.id, location, delta: quantity, notes: notes.trim() });
      onSuccess?.();
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleClose = () => {
    if (adjust.isPending) return;
    setError('');
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} title="Adjust product stock">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/60">
          <p className="text-xs text-slate-500 dark:text-slate-400">Product</p>
          <p className="mt-1 break-words text-sm font-bold text-slate-900 dark:text-white">{product.name}</p>
          {product.sku && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">SKU: {product.sku}</p>}
        </div>

        <Select label="Stock location" value={location} onChange={(event) => { setLocation(event.target.value); setError(''); }}>
          <option value="">Select location...</option>
          {availableLocations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </Select>

        <Input label="Adjustment quantity" type="number" step="1" value={delta} onChange={(event) => { setDelta(event.target.value); setError(''); }} placeholder="e.g. 5 or -3" />
        <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">Enter a positive quantity to add stock or a negative quantity to remove stock.</p>

        {delta.trim() !== '' && Number.isFinite(quantity) && quantity !== 0 && (
          <div className={`rounded-xl border p-3 text-sm ${isRemoval ? 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300' : 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-300'}`}>
            {isRemoval ? `You are removing ${formatNumber(Math.abs(quantity), 0)} units from this location.` : `You are adding ${formatNumber(quantity, 0)} units to this location.`}
          </div>
        )}

        <Input label="Notes (optional)" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Reason for this adjustment" />

        {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400">{error}</div>}

        <div className="sticky bottom-[-1rem] -mx-4 -mb-4 mt-1 flex w-[calc(100%+2rem)] flex-row gap-2 border-t border-slate-200 bg-white px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3 shadow-[0_-8px_24px_rgba(15,23,42,0.06)] dark:border-slate-700 dark:bg-slate-900 sm:-mx-5 sm:-mb-5 sm:w-[calc(100%+2.5rem)] sm:px-5">
          <Button type="button" variant="secondary" onClick={handleClose} disabled={adjust.isPending} className="w-full flex-1">Cancel</Button>
          <Button type="submit" loading={adjust.isPending} disabled={!validAdjustment || adjust.isPending} className="w-full flex-1">Apply adjustment</Button>
        </div>
      </form>
    </Modal>
  );
}