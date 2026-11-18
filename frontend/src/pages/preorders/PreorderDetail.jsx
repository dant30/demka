import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDetail, useAction, useList, useQueueReceipt } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';

export default function PreorderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: order, isLoading, refetch } = useDetail('preorder', endpoints.preorders.staffDetail(id), id);
  const [showDeliver, setShowDeliver] = useState(false);

  const confirm = useAction('preorder', endpoints.preorders.confirm, { invalidate: ['preorder'] });
  const prepare = useAction('preorder', endpoints.preorders.prepare, { invalidate: ['preorder'] });
  const ready = useAction('preorder', endpoints.preorders.ready, { invalidate: ['preorder'] });
  const cancel = useAction('preorder', endpoints.preorders.cancel, { invalidate: ['preorder'] });

  if (isLoading) return <div>Loading...</div>;
  if (!order) return <div>Not found</div>;

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">{order.preorder_number}</h1>
          <p className="text-sm text-slate-500">
            {order.customer_name} · {order.customer_phone} · {order.status_display}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {order.status === 'SUBMITTED' && (
            <Button onClick={() => confirm.mutate({ id })} loading={confirm.isPending}>Confirm</Button>
          )}
          {order.status === 'CONFIRMED' && (
            <Button onClick={() => prepare.mutate({ id })} loading={prepare.isPending}>Start Preparing</Button>
          )}
          {order.status === 'IN_PREPARATION' && (
            <Button onClick={() => ready.mutate({ id })} loading={ready.isPending}>Mark Ready</Button>
          )}
          {order.status === 'READY' && (
            <Button onClick={() => setShowDeliver(true)}>Deliver</Button>
          )}
          {!['DELIVERED', 'CANCELLED'].includes(order.status) && (
            <Button variant="danger" onClick={() => {
              const reason = prompt('Cancel reason:');
              if (reason) cancel.mutate({ id, reason });
            }}>Cancel</Button>
          )}
        </div>
      </div>

      <div className="card p-0">
        <table className="table">
          <thead><tr><th>Item</th><th className="text-right">Qty</th><th className="text-right">Est. Price</th><th className="text-right">Line</th></tr></thead>
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

      <div className="card flex justify-between items-center text-lg font-semibold">
        <span>Estimated Total</span>
        <span>{formatKes(order.total_estimated)}</span>
      </div>

      {order.notes && (
        <div className="card">
          <div className="text-xs text-slate-500 uppercase mb-1">Customer Notes</div>
          <p className="text-sm">{order.notes}</p>
        </div>
      )}

      <DeliverModal
        open={showDeliver}
        onClose={() => setShowDeliver(false)}
        order={order}
        onSuccess={() => { setShowDeliver(false); refetch(); navigate(`/sales`); }}
      />
    </div>
  );
}

function DeliverModal({ open, onClose, order, onSuccess }) {
  const { data: locations } = useList('locations', endpoints.inventory.locations);
  const { data: methods } = useList('payment-methods', endpoints.payments.methods);
  const [location, setLocation] = useState('');
  const [method, setMethod] = useState('CASH');
  const [amountPaid, setAmountPaid] = useState(order.total_estimated);
  const deliver = useAction('preorder', endpoints.preorders.deliver, { onSuccess });

  return (
    <Modal open={open} onClose={onClose} title="Deliver Preorder" size="lg">
      <div className="space-y-3">
        <Select label="Location" value={location} onChange={(e) => setLocation(e.target.value)}>
          <option value="">Select...</option>
          {(locations?.results || locations || []).map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </Select>
        <Select label="Payment Method" value={method} onChange={(e) => setMethod(e.target.value)}>
          {(methods || []).map((m) => <option key={m.id} value={m.code}>{m.name}</option>)}
        </Select>
        <Input label="Amount Paid" type="number" step="0.01" value={amountPaid} onChange={(e) => setAmountPaid(e.target.value)} />
        <Button
          onClick={() => deliver.mutate({ id: order.id, location, payment_method: method, amount_paid: amountPaid })}
          loading={deliver.isPending}
          className="w-full"
        >
          Deliver & Create Sale
        </Button>
      </div>
    </Modal>
  );
}