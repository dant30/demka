import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import DatePicker from '@/components/ui/DatePicker';
import PageHeader from '@/components/ui/PageHeader';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Filter from '@/components/ui/Filter';

export default function SalesList() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    search: '', channel: '', status: '', sale_type: '',
    is_credit_sale: '', start: '', end: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['sales-list', page, filters],
    queryFn: async () => (await api.get(endpoints.sales.list, {
      params: { page, page_size: 25, ...clean(filters) },
    })).data,
  });

  const sales = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const columns = [
    { key: 'sale_number', label: 'Sale #', render: (r) => (
      <Link to={`/sales/${r.id}`} className="text-brand-600 hover:underline font-medium">
        {r.sale_number}
      </Link>
    )},
    { key: 'created_at', label: 'Date', render: (r) => formatDateTime(r.created_at) },
    { key: 'customer_name', label: 'Customer' },
    { key: 'channel_display', label: 'Channel' },
    { key: 'status_display', label: 'Status', render: (r) => (
      <Badge variant={statusVariant(r.status)}>{r.status_display}</Badge>
    )},
    { key: 'total', label: 'Total', align: 'right', render: (r) => formatKes(r.total) },
    { key: 'balance_due', label: 'Balance', align: 'right', render: (r) => (
      <span className={Number(r.balance_due) > 0 ? 'text-red-600 font-semibold' : ''}>
        {formatKes(r.balance_due)}
      </span>
    )},
    { key: 'agent_name', label: 'Agent' },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Sales"
        description="Review transactions by date, channel, and payment status."
        actions={<Link to="/pos" className="btn-primary">New Sale</Link>}
      />

      <Filter title="Sales filters" contentClassName="grid grid-cols-1 gap-3 md:grid-cols-4">
        <Input
          placeholder="Search sale # or customer..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="md:col-span-2"
        />
        <Select
          value={filters.channel}
          onChange={(e) => setFilters({ ...filters, channel: e.target.value })}
        >
          <option value="">All channels</option>
          <option value="SHOP">Shop</option>
          <option value="FIELD">Field</option>
        </Select>
        <Select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        >
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="PAID">Paid</option>
          <option value="PARTIAL">Partial</option>
          <option value="CANCELLED">Cancelled</option>
          <option value="RETURNED">Returned</option>
        </Select>
        <DatePicker
          label="From"
          value={filters.start}
          onChange={(value) => setFilters({ ...filters, start: value })}
        />
        <DatePicker
          label="To"
          value={filters.end}
          onChange={(value) => setFilters({ ...filters, end: value })}
        />
        <Select
          label="Credit"
          value={filters.is_credit_sale}
          onChange={(e) => setFilters({ ...filters, is_credit_sale: e.target.value })}
        >
          <option value="">All</option>
          <option value="true">Credit only</option>
          <option value="false">Cash only</option>
        </Select>
        <div className="flex items-end">
          <Button
            variant="secondary"
            onClick={() => setFilters({ search: '', channel: '', status: '', sale_type: '', is_credit_sale: '', start: '', end: '' })}
            className="w-full"
          >
            Reset
          </Button>
        </div>
      </Filter>

      <DataTable
        columns={columns}
        rows={sales}
        loading={isLoading}
        onRowClick={(r) => navigate(`/sales/${r.id}`)}
        empty="No sales match your filters."
      />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}

function clean(obj) {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== '' && v !== null && v !== undefined));
}

function statusVariant(status) {
  const map = {
    DRAFT: 'neutral', CONFIRMED: 'success',
    PAID: 'success', PARTIAL: 'warning',
    CANCELLED: 'danger', RETURNED: 'danger',
    INVOICED: 'neutral',
  };
  return map[status] || 'neutral';
}