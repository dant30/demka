import { useQuery } from '@tanstack/react-query';
import { portalApi } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import Badge from '@/components/ui/Badge';

const STATUS_VARIANT = {
  SUBMITTED: 'neutral',
  CONFIRMED: 'success',
  IN_PREPARATION: 'warning',
  READY: 'success',
  DELIVERED: 'success',
  CANCELLED: 'danger',
};

export default function PortalOrders() {
  const { data, isLoading } = useQuery({
    queryKey: ['portal-orders'],
    queryFn: async () => (await portalApi.get(endpoints.preorders.portal.orders)).data,
    refetchInterval: 30_000,
  });

  const orders = data?.results || data || [];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex justify-between">
          <h1 className="font-bold text-lg">My Orders</h1>
          <a href="/portal" className="text-sm text-brand-600 hover:underline">← Back to catalog</a>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-3">
        {isLoading && <div>Loading...</div>}
        {!isLoading && orders.length === 0 && (
          <div className="card text-center py-12 text-slate-500">
            You haven't placed any orders yet.
          </div>
        )}
        {orders.map((o) => (
          <div key={o.id} className="card">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="font-semibold">{o.preorder_number}</div>
                <div className="text-xs text-slate-500">{formatDateTime(o.created_at)}</div>
              </div>
              <Badge variant={STATUS_VARIANT[o.status] || 'neutral'}>
                {o.status_display}
              </Badge>
            </div>
            <div className="text-sm text-slate-600">
              {o.item_count} item{o.item_count !== 1 ? 's' : ''} · Est. {formatKes(o.total_estimated)}
            </div>
            <a href={`/portal/orders/${o.id}`} className="mt-3 inline-block text-brand-600 text-sm hover:underline">
              View details →
            </a>
          </div>
        ))}
      </main>
    </div>
  );
}