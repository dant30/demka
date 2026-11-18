import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import PageHeader from '@/components/ui/PageHeader';
import Button from '@/components/ui/Button';
import Filter from '@/components/ui/Filter';

export default function CustomersList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');

  const { data, isLoading } = useList('customers', endpoints.customers.list, {
    page, search: search || undefined, customer_type: type || undefined,
  });
  const customers = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const columns = [
    { key: 'code', label: 'Code', render: (r) => (
      <Link to={`/customers/${r.id}`} className="text-brand-600 font-medium hover:underline">
        {r.code}
      </Link>
    )},
    { key: 'name', label: 'Name' },
    { key: 'phone', label: 'Phone' },
    { key: 'customer_type_display', label: 'Type' },
    { key: 'credit_limit', label: 'Credit Limit', align: 'right', render: (r) => formatKes(r.credit_limit) },
    { key: 'current_balance', label: 'Balance', align: 'right', render: (r) => (
      <span className={Number(r.current_balance) > 0 ? 'text-red-600 font-semibold' : 'text-green-600'}>
        {formatKes(r.current_balance)}
      </span>
    )},
    { key: 'is_active', label: 'Active', render: (r) => r.is_active ? '✓' : '✗' },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Customers"
        description="Search customer accounts, balances, and contact details."
        actions={<Link to="/customers/new" className="btn-primary">+ New Customer</Link>}
      />

      <Filter title="Customer filters" contentClassName="grid grid-cols-1 gap-3 md:grid-cols-3">
        <Input
          placeholder="Search name, phone, code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="md:col-span-2"
        />
        <Select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">All types</option>
          <option value="RETAIL">Retail</option>
          <option value="RESELLER">Reseller</option>
          <option value="WALK_IN">Walk-in</option>
        </Select>
      </Filter>

      <DataTable columns={columns} rows={customers} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}