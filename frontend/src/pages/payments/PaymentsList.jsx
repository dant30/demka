import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import PageHeader from '@/components/ui/PageHeader';
import Select from '@/components/ui/Select';
import Input from '@/components/ui/Input';
import Filter from '@/components/ui/Filter';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import { useAuth } from '@/hooks/useAuth';

export default function PaymentsList() {
  const { isBoss } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [method, setMethod] = useState('');
  const [status, setStatus] = useState('');
  const [paymentToReverse, setPaymentToReverse] = useState(null);
  const [reason, setReason] = useState('');
  const [reverseError, setReverseError] = useState('');
  const { data, isLoading } = useList('payments', endpoints.payments.list, {
    page, search: search || undefined, method: method || undefined, status: status || undefined,
  });
  const reversePayment = useMutation({
    mutationFn: async () => (await api.post(
      endpoints.payments.reverse(paymentToReverse.id),
      { reason: reason.trim() },
    )).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      setPaymentToReverse(null);
      setReason('');
      setReverseError('');
    },
    onError: (error) => setReverseError(extractError(error)),
  });
  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;
  const clearFilters = () => {
    setSearch('');
    setMethod('');
    setStatus('');
    setPage(1);
  };

  const columns = [
    { key: 'payment_number', label: 'Payment #', render: (r) => (
      <span className="font-medium">{r.payment_number}</span>
    )},
    { key: 'received_at', label: 'Date', render: (r) => formatDateTime(r.received_at) },
    { key: 'customer_name', label: 'Customer' },
    { key: 'method_name', label: 'Method' },
    { key: 'amount', label: 'Amount', align: 'right', render: (r) => formatKes(r.amount) },
    { key: 'reference', label: 'Reference', render: (r) => r.reference || '—' },
    { key: 'status_display', label: 'Status' },
    { key: 'sale_number', label: 'Sale', render: (r) => r.sale_number || '—' },
    {
      key: 'actions',
      label: 'Actions',
      mobileFullWidth: true,
      render: (payment) => isBoss && payment.status === 'CONFIRMED' && (
        <Button
          size="sm"
          variant="danger"
          className="min-h-11 w-full sm:min-h-8 sm:w-auto"
          onClick={() => {
            setPaymentToReverse(payment);
            setReason('');
            setReverseError('');
          }}
        >
          Reverse payment
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Payments"
        description="Review incoming payments and their reconciliation status."
        actions={<Link to="/payments/mpesa" className="btn-secondary">M-Pesa Reconcile</Link>}
      />
      <Filter
        title="Payment filters"
        headerContent={(
          <Input
            type="search"
            aria-label="Search payments by number, customer, or reference"
            placeholder="Search payments..."
            value={search}
            onChange={(event) => { setSearch(event.target.value); setPage(1); }}
          />
        )}
        activeCount={[method, status].filter(Boolean).length}
        onClear={clearFilters}
        showClear
        contentClassName="grid grid-cols-1 gap-3 md:grid-cols-2"
      >
        <Select value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="">All methods</option>
          <option value="CASH">Cash</option>
          <option value="MPESA">M-Pesa</option>
          <option value="CHEQUE">Cheque</option>
          <option value="BANK_TRANSFER">Bank Transfer</option>
        </Select>
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="PENDING">Pending</option>
          <option value="REVERSED">Reversed</option>
        </Select>
      </Filter>
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />

      <Modal
        open={Boolean(paymentToReverse)}
        onClose={() => !reversePayment.isPending && setPaymentToReverse(null)}
        title="Reverse payment"
        size="sm"
        footer={(
          <div className="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button
              variant="secondary"
              className="w-full sm:w-auto"
              onClick={() => setPaymentToReverse(null)}
              disabled={reversePayment.isPending}
            >
              Keep payment
            </Button>
            <Button
              variant="danger"
              className="w-full sm:w-auto"
              onClick={() => reversePayment.mutate()}
              loading={reversePayment.isPending}
            >
              Confirm reversal
            </Button>
          </div>
        )}
      >
        <div className="space-y-3">
          <p className="text-sm leading-6 text-slate-600">
            Reverse {paymentToReverse?.payment_number} for {formatKes(paymentToReverse?.amount)}?
            This restores the customer balance and updates any linked sale.
          </p>
          <Input
            label="Reason (optional)"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            maxLength={240}
          />
          {reverseError && <p role="alert" className="text-sm text-red-700">{reverseError}</p>}
        </div>
      </Modal>
    </div>
  );
}