import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDate } from '@/utils/dates';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import PageHeader from '@/components/ui/PageHeader';
import Filter from '@/components/ui/Filter';

export default function PurchaseOrdersList() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const { data, isLoading } = useList('pos', endpoints.purchasing.pos, {
    page, status: status || undefined, search: search || undefined,
  });
  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;
  const clearFilters = () => {
    setStatus('');
    setSearch('');
    setPage(1);
  };

  const columns = [
    { key: 'po_number', label: 'PO #', render: (r) => (
      <Link to={`/purchasing/pos/${r.id}`} className="text-brand-600 font-medium hover:underline">
        {r.po_number}
      </Link>
    )},
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'status_display', label: 'Status' },
    { key: 'item_count', label: 'Items', align: 'right' },
    { key: 'total', label: 'Total', align: 'right', render: (r) => formatKes(r.total) },
    { key: 'expected_date', label: 'Expected', render: (r) => formatDate(r.expected_date) },
    { key: 'created_at', label: 'Created', render: (r) => formatDate(r.created_at) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Purchase Orders"
        description="Track supplier orders from draft through receipt."
        actions={<Link to="/purchasing/pos/new" className="btn-primary">+ New PO</Link>}
      />
      <Filter title="Purchase order filters" activeCount={[status, search].filter(Boolean).length} onClear={clearFilters} showClear contentClassName="grid grid-cols-1 gap-3 md:grid-cols-3">
        <Input placeholder="Search PO # or supplier..." value={search} onChange={(e) => setSearch(e.target.value)} className="md:col-span-2" />
        <Select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="SENT">Sent</option>
          <option value="PARTIAL">Partial</option>
          <option value="RECEIVED">Received</option>
          <option value="CANCELLED">Cancelled</option>
        </Select>
      </Filter>
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}