import { useState } from 'react';
import { useList, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import PageHeader from '@/components/ui/PageHeader';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import ConfirmDialong from '@/components/ui/ConfirmDialong';
import Filter from '@/components/ui/Filter';

const PAGE_SIZE = 25;

export default function SpecialOrdersList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [confirmAction, setConfirmAction] = useState(null);
  const [cancelOrder, setCancelOrder] = useState(null);
  const [cancelReason, setCancelReason] = useState('');

  const { data, isLoading } = useList('special-orders', endpoints.sales.specialOrders, {
    page,
    page_size: PAGE_SIZE,
    search: search || undefined,
    status: status || undefined,
  });
  const markArrived = useAction('special-orders', endpoints.sales.soMarkArrived, { invalidate: ['special-orders'] });
  const markDelivered = useAction('special-orders', endpoints.sales.soMarkDelivered, { invalidate: ['special-orders'] });
  const cancel = useAction('special-orders', endpoints.sales.soCancel, { invalidate: ['special-orders'] });

  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / PAGE_SIZE) : 0;
  const clearFilters = () => {
    setSearch('');
    setStatus('');
    setPage(1);
  };

  const runConfirmedAction = async () => {
    const action = confirmAction?.type === 'arrived' ? markArrived : markDelivered;
    await action.mutateAsync({ id: confirmAction.order.id });
  };

  const submitCancel = async () => {
    await cancel.mutateAsync({ id: cancelOrder.id, reason: cancelReason.trim() });
    setCancelOrder(null);
    setCancelReason('');
  };

  const columns = [
    {
      key: 'product_name',
      label: 'Product',
      render: (order) => <span><span className="font-medium">{order.product_name}</span><span className="block text-xs text-slate-500">{order.product_sku}</span></span>,
    },
    { key: 'sale_number', label: 'Sale #' },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'quantity', label: 'Qty', align: 'right' },
    {
      key: 'status_display',
      label: 'Status',
      render: (order) => <Badge variant={statusVariant(order.status)}>{order.status_display}</Badge>,
    },
    { key: 'expected_arrival_date', label: 'Expected' },
    { key: 'customer_deposit', label: 'Deposit', align: 'right', render: (order) => formatKes(order.customer_deposit) },
    {
      key: 'actions',
      label: 'Actions',
      render: (order) => (
        <div className="flex flex-wrap gap-2">
          {order.status === 'ORDERED' && (
            <Button size="sm" variant="secondary" onClick={() => setConfirmAction({ type: 'arrived', order })}>
              Mark Arrived
            </Button>
          )}
          {['ORDERED', 'ARRIVED'].includes(order.status) && (
            <Button size="sm" onClick={() => setConfirmAction({ type: 'delivered', order })}>
              Deliver
            </Button>
          )}
          {!['DELIVERED', 'CANCELLED'].includes(order.status) && (
            <Button size="sm" variant="danger" onClick={() => { setCancelOrder(order); setCancelReason(''); }}>
              Cancel
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Special Orders" description="Track products ordered for customers through delivery." />
      <Filter
        title="Special order filters"
        headerContent={(
          <Input
            type="search"
            aria-label="Search special orders by sale number, SKU, or product"
            placeholder="Search special orders..."
            value={search}
            onChange={(event) => { setSearch(event.target.value); setPage(1); }}
          />
        )}
        activeCount={status ? 1 : 0}
        onClear={clearFilters}
        showClear
      >
        <Select label="Status" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="ORDERED">Ordered</option>
          <option value="ARRIVED">Arrived</option>
          <option value="DELIVERED">Delivered</option>
          <option value="CANCELLED">Cancelled</option>
        </Select>
      </Filter>
      <DataTable
        columns={columns}
        rows={rows}
        loading={isLoading}
        empty="No special orders match these filters."
        caption="Special orders"
      />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />

      <ConfirmDialong
        open={Boolean(confirmAction)}
        onClose={() => setConfirmAction(null)}
        onConfirm={runConfirmedAction}
        title={confirmAction?.type === 'arrived' ? 'Mark order arrived?' : 'Deliver special order?'}
        description={confirmAction?.type === 'arrived'
          ? `Mark ${confirmAction?.order.product_name} as arrived?`
          : `Deliver ${confirmAction?.order.product_name} to the customer? This deducts stock at the sale location.`}
        confirmLabel={confirmAction?.type === 'arrived' ? 'Mark Arrived' : 'Deliver Order'}
        variant={confirmAction?.type === 'arrived' ? 'primary' : 'danger'}
        loading={markArrived.isPending || markDelivered.isPending}
      />

      <Modal open={Boolean(cancelOrder)} onClose={() => setCancelOrder(null)} title="Cancel Special Order">
        <div className="space-y-3">
          <p className="text-sm text-slate-600">Cancel the order for {cancelOrder?.product_name}?</p>
          <label className="label" htmlFor="special-order-cancel-reason">Reason</label>
          <textarea
            id="special-order-cancel-reason"
            className="input min-h-24 w-full"
            value={cancelReason}
            onChange={(event) => setCancelReason(event.target.value)}
            rows={3}
          />
          <Button variant="danger" onClick={submitCancel} loading={cancel.isPending} className="w-full">
            Cancel Order
          </Button>
        </div>
      </Modal>
    </div>
  );
}

function statusVariant(status) {
  if (status === 'DELIVERED') return 'success';
  if (status === 'ARRIVED') return 'warning';
  if (status === 'CANCELLED') return 'danger';
  return 'neutral';
}