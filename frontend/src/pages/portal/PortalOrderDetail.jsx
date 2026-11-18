import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { portalApi } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import ConfirmDialong from '@/components/ui/ConfirmDialong';

export default function PortalOrderDetail() {
  const { id } = useParams();
  const [confirmCancel, setConfirmCancel] = useState(false);
  const { data: order, isLoading } = useQuery({
    queryKey: ['portal-order', id],
    queryFn: async () => (await portalApi.get(endpoints.preorders.portal.orderDetail(id))).data,
  });

  const cancel = useMutation({
    mutationFn: async () =>
      (await portalApi.post(endpoints.preorders.portal.orderCancel(id), {})).data,
  });

  if (isLoading) return <div>Loading...</div>;
  if (!order) return <div>Not found</div>;

  const canCancel = order.status === 'SUBMITTED';

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex justify-between">
          <h1 className="font-bold text-lg">{order.preorder_number}</h1>
          <a href="/portal/orders" className="text-sm text-brand-600 hover:underline">← Back</a>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-4">
        <div className="card">
          <div className="text-sm text-slate-500">Status</div>
          <div className="font-semibold text-lg">{order.status_display}</div>
          <div className="text-xs text-slate-500 mt-1">Placed {formatDateTime(order.created_at)}</div>
        </div>

        <div className="card p-0">
          <table className="table">
            <thead>
              <tr><th>Item</th><th className="text-right">Qty</th><th className="text-right">Price</th><th className="text-right">Total</th></tr>
            </thead>
            <tbody>
              {order.items.map((it) => (
                <tr key={it.id}>
                  <td>
                    <div className="font-medium">{it.product_name}</div>
                    <div className="text-xs text-slate-500">{it.product_sku}</div>
                  </td>
                  <td className="text-right">{it.quantity}</td>
                  <td className="text-right">{formatKes(it.effective_unit_price)}</td>
                  <td className="text-right font-medium">{formatKes(it.line_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card flex justify-between text-lg font-semibold">
          <span>Estimated Total</span>
          <span>{formatKes(order.total_estimated)}</span>
        </div>

        {canCancel && (
          <button
            onClick={() => setConfirmCancel(true)}
            className="btn-danger w-full"
            disabled={cancel.isPending}
          >
            Cancel Order
          </button>
        )}
        <ConfirmDialong
          open={confirmCancel}
          onClose={() => setConfirmCancel(false)}
          onConfirm={() => cancel.mutateAsync()}
          title="Cancel this order?"
          description="This order will be cancelled and cannot be resumed."
          confirmLabel="Cancel order"
          loading={cancel.isPending}
        />
      </main>
    </div>
  );
}