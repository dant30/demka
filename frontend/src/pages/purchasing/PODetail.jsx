import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDetail, useAction, useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDate, formatDateTime } from '@/utils/dates';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import ConfirmDialong from '@/components/ui/ConfirmDialong';

export default function PODetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [confirmCancel, setConfirmCancel] = useState(false);
  const { data: po, isLoading, refetch } = useDetail('po', endpoints.purchasing.poDetail(id), id);
  const send = useAction('po', endpoints.purchasing.poSend, { invalidate: ['po'] });
  const cancel = useAction('po', endpoints.purchasing.poCancel, { invalidate: ['po'] });

  if (isLoading) return <div>Loading...</div>;
  if (!po) return <div>Not found</div>;

  const canSend = po.status === 'DRAFT';
  const canCancel = ['DRAFT', 'SENT'].includes(po.status);
  const canReceive = ['SENT', 'PARTIAL'].includes(po.status);

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">{po.po_number}</h1>
          <p className="text-sm text-slate-500">{po.supplier_name} · {po.status_display}</p>
        </div>
        <div className="flex gap-2">
          {canSend && <Button onClick={() => send.mutate({ id: po.id })}>Send to Supplier</Button>}
          {canReceive && <Button onClick={() => navigate(`/purchasing/receive/${po.id}`)}>Receive Goods</Button>}
          {canCancel && <Button variant="danger" onClick={() => setConfirmCancel(true)}>Cancel</Button>}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Expected" value={formatDate(po.expected_date)} />
        <Stat label="Subtotal" value={formatKes(po.subtotal)} />
        <Stat label="Tax" value={formatKes(po.tax)} />
        <Stat label="Total" value={formatKes(po.total)} />
      </div>

      <div className="card p-0">
        <table className="table">
          <thead><tr><th>Product</th><th className="text-right">Ordered</th><th className="text-right">Received</th><th className="text-right">Remaining</th><th className="text-right">Unit Cost</th><th className="text-right">Total</th></tr></thead>
          <tbody>
            {po.items.map((it) => (
              <tr key={it.id}>
                <td>
                  <div className="font-medium">{it.product_name}</div>
                  <div className="text-xs text-slate-500">{it.product_sku}</div>
                </td>
                <td className="text-right">{it.quantity_ordered}</td>
                <td className="text-right">{it.quantity_received}</td>
                <td className="text-right">{it.remaining_quantity}</td>
                <td className="text-right">{formatKes(it.unit_cost)}</td>
                <td className="text-right font-medium">{formatKes(it.line_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {po.grns && po.grns.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Goods Received Notes</h3>
          <table className="table">
            <thead><tr><th>GRN #</th><th>Received</th><th></th></tr></thead>
            <tbody>
              {po.grns.map((g) => (
                <tr key={g.id}>
                  <td>{g.grn_number}</td>
                  <td>{formatDateTime(g.received_at)}</td>
                  <td><a href={`/purchasing/grns/${g.id}`} className="text-brand-600 text-sm">View</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialong
        open={confirmCancel}
        onClose={() => setConfirmCancel(false)}
        onConfirm={async () => {
          await cancel.mutateAsync({ id: po.id });
          await refetch();
        }}
        title="Cancel purchase order?"
        description={`Purchase order ${po.po_number} will be cancelled.`}
        confirmLabel="Cancel purchase order"
        loading={cancel.isPending}
      />
    </div>
  );
}

const Stat = ({ label, value }) => (
  <div className="card">
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className="mt-1 font-semibold">{value}</div>
  </div>
);