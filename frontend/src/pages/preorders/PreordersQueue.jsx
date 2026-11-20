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
import Filter from '@/components/ui/Filter';

export default function PreordersQueue() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('SUBMITTED');
  const { data, isLoading } = useList('preorders-staff', endpoints.preorders.staffList, {
    page, status: status || undefined,
  });
  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;
  const clearFilters = () => {
    setStatus('SUBMITTED');
    setPage(1);
  };

  const columns = [
    { key: 'preorder_number', label: 'Order #', render: (r) => (
      <Link to={`/preorders/${r.id}`} className="text-brand-600 font-medium hover:underline">
        {r.preorder_number}
      </Link>
    )},
    { key: 'status_display', label: 'Status' },
    { key: 'total_estimated', label: 'Est. Total', align: 'right', render: (r) => formatKes(r.total_estimated) },
    { key: 'item_count', label: 'Items', align: 'right' },
    { key: 'preferred_pickup_date', label: 'Pickup' },
    { key: 'created_at', label: 'Placed', render: (r) => formatDateTime(r.created_at) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Preorders" description="Track customer orders from submission through delivery." />
      <Filter title="Preorder filters" activeCount={status !== 'SUBMITTED' ? 1 : 0} onClear={clearFilters} showClear>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="max-w-xs">
          <option value="">All statuses</option>
          <option value="SUBMITTED">Submitted</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="IN_PREPARATION">In Preparation</option>
          <option value="READY">Ready</option>
          <option value="DELIVERED">Delivered</option>
          <option value="CANCELLED">Cancelled</option>
        </Select>
      </Filter>
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}