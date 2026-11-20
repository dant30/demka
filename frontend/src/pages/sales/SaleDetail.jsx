import { useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useDetail, useCreate, useAction, useQueueReceipt } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { useAuth } from '@/hooks/useAuth';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import { useBluetoothPrinter } from '@/hooks/useBluetoothPrinter';
import Button from '@/components/ui/Button';
import CheckBox from '@/components/ui/CheckBox';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import CircularProgress from '@/components/ui/CircularProgress';

export default function SaleDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const receiptJob = searchParams.get('receiptJob');
  const { isBoss } = useAuth();

  const { data: sale, isLoading, refetch } = useDetail(
    'sale', endpoints.sales.detail(id), id
  );
  const { data: returns } = useDetail(
    'sale-returns', endpoints.sales.returns(id), id
  );
  const queueReceipt = useQueueReceipt();
  const bt = useBluetoothPrinter();

  const [showPayment, setShowPayment] = useState(false);
  const [showCancel, setShowCancel] = useState(false);
  const [showReturn, setShowReturn] = useState(false);

  if (isLoading) return <div>Loading...</div>;
  if (!sale) return <div>Sale not found.</div>;

  const canPay = ['CONFIRMED', 'PARTIAL'].includes(sale.status) && Number(sale.balance_due) > 0;
  const canCancel = isBoss && ['DRAFT', 'CONFIRMED'].includes(sale.status) && Number(sale.amount_paid) === 0;
  const canReturn = ['CONFIRMED', 'PAID', 'PARTIAL'].includes(sale.status);
  const totalAmount = Number(sale.total) || 0;
  const paidAmount = Number(sale.amount_paid) || 0;
  const paymentPercentage = totalAmount > 0
    ? Math.min(100, Math.max(0, Math.round((paidAmount / totalAmount) * 100)))
    : 0;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{sale.sale_number}</h1>
          <p className="text-sm text-slate-500">{formatDateTime(sale.confirmed_at)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={async () => {
            const job = await queueReceipt.mutateAsync(sale.id);
            alert(`Queued receipt (job #${job.id}).`);
          }}>
            Reprint
          </Button>
          {bt.supported && (
            <Button
              variant="primary"
              onClick={async () => {
                const jobId = receiptJob || (await queueReceipt.mutateAsync(sale.id)).id;
                await bt.printJob(jobId);
              }}
              loading={bt.busy}
            >
              Bluetooth Print
            </Button>
          )}
          {canPay && <Button onClick={() => setShowPayment(true)}>Record Payment</Button>}
          {canReturn && <Button variant="secondary" onClick={() => setShowReturn(true)}>Return Items</Button>}
          {canCancel && <Button variant="danger" onClick={() => setShowCancel(true)}>Cancel Sale</Button>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Info label="Customer" value={sale.customer_name} />
        <Info label="Channel" value={sale.channel_display} />
        <Info label="Status" value={sale.status_display} />
        <Info label="Agent" value={sale.agent_name} />
        <Info label="Location" value={sale.location_name} />
        <Info label="Payment" value={sale.is_credit_sale ? 'Credit' : 'Paid'} />
      </div>

      <div className="card p-0">
        <table className="table">
          <thead>
            <tr>
              <th>Item</th>
              <th className="text-right">Qty</th>
              <th className="text-right">Returned</th>
              <th className="text-right">Price</th>
              <th className="text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {sale.items.map((it) => (
              <tr key={it.id}>
                <td>
                  <div className="font-medium">{it.product_name}</div>
                  <div className="text-xs text-slate-500">{it.product_sku}</div>
                </td>
                <td className="text-right">{it.quantity}</td>
                <td className="text-right text-slate-500">{it.returned_quantity}</td>
                <td className="text-right">{formatKes(it.unit_price)}</td>
                <td className="text-right font-medium">{formatKes(it.line_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full max-w-sm sm:ml-auto">
          <div className="space-y-2">
            <Row label="Subtotal" value={formatKes(sale.subtotal)} />
            <Row label="VAT" value={formatKes(sale.tax_amount)} />
            {Number(sale.discount_amount) > 0 && (
              <Row label="Discount" value={`-${formatKes(sale.discount_amount)}`} />
            )}
            <Row label="Total" value={formatKes(sale.total)} bold />
            <Row label="Paid" value={formatKes(sale.amount_paid)} />
            {Number(sale.balance_due) > 0 && (
              <Row label="Balance" value={formatKes(sale.balance_due)} danger />
            )}
          </div>
        </div>
        <CircularProgress
          value={paidAmount}
          max={totalAmount}
          size="lg"
          variant={Number(sale.balance_due) > 0 ? 'primary' : 'success'}
          label="Payment progress"
          valueLabel={`${paymentPercentage}%`}
          description={`${formatKes(sale.amount_paid)} paid of ${formatKes(sale.total)}`}
        />
      </div>

      {returns && returns.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Returns Against This Sale</h3>
          <table className="table">
            <thead><tr><th>Return #</th><th>Status</th><th className="text-right">Refund</th><th>Date</th></tr></thead>
            <tbody>
              {returns.map((r) => (
                <tr key={r.id}>
                  <td>{r.return_number}</td>
                  <td>{r.status_display}</td>
                  <td className="text-right">{formatKes(r.refund_amount)}</td>
                  <td>{formatDateTime(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <PaymentModalInline open={showPayment} onClose={() => setShowPayment(false)} sale={sale} onSuccess={refetch} />
      <CancelSaleModal open={showCancel} onClose={() => setShowCancel(false)} sale={sale} onSuccess={refetch} />
      <ReturnSaleModal open={showReturn} onClose={() => setShowReturn(false)} sale={sale} onSuccess={refetch} />
    </div>
  );
}

// ---- Modals ----

function PaymentModalInline({ open, onClose, sale, onSuccess }) {
  const [amount, setAmount] = useState(sale?.balance_due || '');
  const [method, setMethod] = useState('CASH');
  const [reference, setReference] = useState('');
  const apply = useAction('sale', endpoints.sales.applyPayment, { invalidate: ['sale', 'sales-list'] });

  const submit = async () => {
    try {
      await apply.mutateAsync({
        id: sale.id,
        amount, method, reference,
        mpesa_phone: method === 'MPESA' ? reference : '',
        mpesa_receipt_number: method === 'MPESA' ? reference : '',
      });
      onSuccess?.();
      onClose();
    } catch (err) {
      alert(err?.response?.data?.error?.message || 'Payment failed');
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Record Payment">
      <div className="space-y-3">
        <Input label="Amount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <Select label="Method" value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="CASH">Cash</option>
          <option value="MPESA">M-Pesa</option>
          <option value="CHEQUE">Cheque</option>
          <option value="BANK_TRANSFER">Bank Transfer</option>
        </Select>
        {method !== 'CASH' && (
          <Input label="Reference" value={reference} onChange={(e) => setReference(e.target.value)} />
        )}
        <Button onClick={submit} loading={apply.isPending} className="w-full">Apply Payment</Button>
      </div>
    </Modal>
  );
}

function CancelSaleModal({ open, onClose, sale, onSuccess }) {
  const [reason, setReason] = useState('');
  const cancel = useAction('sale', endpoints.sales.cancel, { invalidate: ['sale', 'sales-list'] });

  const submit = async () => {
    if (!reason.trim()) return alert('Reason required');
    await cancel.mutateAsync({ id: sale.id, reason });
    onSuccess?.();
    onClose();
  };

  return (
    <Modal open={open} onClose={onClose} title="Cancel Sale">
      <div className="space-y-3">
        <p className="text-sm text-slate-600">This reverses the sale and restores stock.</p>
        <label className="label">Reason</label>
        <textarea className="input" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} />
        <Button variant="danger" onClick={submit} loading={cancel.isPending} className="w-full">
          Confirm Cancel
        </Button>
      </div>
    </Modal>
  );
}

function ReturnSaleModal({ open, onClose, sale, onSuccess }) {
  const [reason, setReason] = useState('');
  const [items, setItems] = useState(() =>
    sale?.items?.map((it) => ({ sale_item: it.id, quantity: 0, restock: true })) || []
  );
  const create = useCreate('sale-returns', endpoints.sales.returnsList, {
    invalidate: ['sale', 'sale-returns'],
    onSuccess: () => { onSuccess?.(); onClose(); },
  });

  const submit = async () => {
    const active = items.filter((i) => Number(i.quantity) > 0);
    if (!active.length) return alert('Select at least one item.');
    await create.mutateAsync({ original_sale: sale.id, reason, items: active });
  };

  return (
    <Modal open={open} onClose={onClose} title="Create Return" size="lg">
      <div className="space-y-3">
        <label className="label">Reason</label>
        <textarea className="input" rows={2} value={reason} onChange={(e) => setReason(e.target.value)} />
        <table className="table">
          <thead><tr><th>Item</th><th>Sold</th><th>Return Qty</th><th>Restock</th></tr></thead>
          <tbody>
            {sale.items.map((it, idx) => {
              const max = Number(it.quantity) - Number(it.returned_quantity);
              return (
                <tr key={it.id}>
                  <td>{it.product_name}</td>
                  <td>{max}</td>
                  <td>
                    <input
                      type="number" min="0" max={max}
                      className="input w-24"
                      value={items[idx]?.quantity}
                      onChange={(e) => {
                        const copy = [...items];
                        copy[idx].quantity = Number(e.target.value);
                        setItems(copy);
                      }}
                    />
                  </td>
                  <td>
                    <CheckBox
                      aria-label={`Restock ${it.product_name}`}
                      checked={items[idx]?.restock}
                      onChange={(e) => {
                        const copy = [...items];
                        copy[idx].restock = e.target.checked;
                        setItems(copy);
                      }}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <Button onClick={submit} loading={create.isPending} className="w-full">Create Return</Button>
      </div>
    </Modal>
  );
}

const Info = ({ label, value }) => (
  <div className="card">
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className="mt-1 font-medium">{value || '—'}</div>
  </div>
);

const Row = ({ label, value, bold, danger }) => (
  <div className={`flex justify-between ${bold ? 'font-semibold text-lg pt-2 border-t' : ''} ${danger ? 'text-red-600' : ''}`}>
    <span>{label}</span><span>{value}</span>
  </div>
);