import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import Input from '@/components/ui/Input';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import PageHeader from '@/components/ui/PageHeader';

export default function SuppliersList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const { data, isLoading } = useList('suppliers', endpoints.suppliers.list, { page, search: search || undefined });
  const suppliers = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const columns = [
    { key: 'code', label: 'Code', render: (r) => (
      <Link to={`/suppliers/${r.id}`} className="text-brand-600 font-medium hover:underline">{r.code}</Link>
    )},
    { key: 'name', label: 'Name' },
    { key: 'phone', label: 'Phone' },
    { key: 'email', label: 'Email' },
    { key: 'payment_terms_days', label: 'Terms', align: 'right', render: (r) => `${r.payment_terms_days}d` },
    { key: 'product_count', label: 'Products', align: 'right' },
    { key: 'is_active', label: 'Active', render: (r) => r.is_active ? '✓' : '✗' },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Suppliers"
        description="Maintain supplier contacts and product relationships."
        actions={<Link to="/suppliers/new" className="btn-primary">+ New Supplier</Link>}
      />
      <div className="w-full max-w-xl">
        <Input
          type="search"
          aria-label="Search suppliers"
          placeholder="Search suppliers..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
      </div>
      <DataTable columns={columns} rows={suppliers} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}