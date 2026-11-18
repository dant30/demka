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

export default function ReturnsList() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const { data, isLoading } = useList('returns-list', endpoints.sales.returnsList, {
    page, status: status || undefined,
  });
  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const columns = [
    { key: 'return_number', label: 'Return #', render: (r) => (
      <Link to={`/sales/returns/${r.id}`} className="text-brand-600 font-medium hover:underline">
        {r.return_number}
      </Link>
    )},
    { key: 'sale_number', label: 'Original Sale' },
    { key: 'customer_name', label: 'Customer' },
    { key: 'status_display', label: 'Status' },
    { key: 'refund_amount', label: 'Refund', align: 'right', render: (r) => formatKes(r.refund_amount) },
    { key: 'created_at', label: 'Date', render: (r) => formatDateTime(r.created_at) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Returns"
        description="Review return requests, approvals, and refunds."
        actions={<Select aria-label="Filter returns by status" value={status} onChange={(e) => setStatus(e.target.value)} className="w-full sm:w-48">
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="COMPLETED">Completed</option>
        </Select>}
      />
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}