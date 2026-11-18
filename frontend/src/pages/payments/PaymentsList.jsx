import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import PageHeader from '@/components/ui/PageHeader';
import Select from '@/components/ui/Select';
import Input from '@/components/ui/Input';

export default function PaymentsList() {
  const [page, setPage] = useState(1);
  const [method, setMethod] = useState('');
  const [status, setStatus] = useState('');
  const { data, isLoading } = useList('payments', endpoints.payments.list, {
    page, method: method || undefined, status: status || undefined,
  });
  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

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
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Payments"
        description="Review incoming payments and their reconciliation status."
        actions={<Link to="/payments/mpesa" className="btn-secondary">M-Pesa Reconcile</Link>}
      />
      <div className="card grid grid-cols-1 md:grid-cols-3 gap-3">
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
      </div>
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}