import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import DataTable from '@/components/ui/DataTable';
import Pagination from '@/components/ui/Pagination';
import PageHeader from '@/components/ui/PageHeader';
import Switch from '@/components/ui/Switch';
import Filter from '@/components/ui/Filter';

export default function InventoryHome() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [lowStock, setLowStock] = useState(false);
  const [categoryId, setCategoryId] = useState('');

  const { data, isLoading } = useList('products', endpoints.inventory.products, {
    page, search: search || undefined, product_type: type || undefined,
    category: categoryId || undefined, needs_reorder: lowStock || undefined, page_size: 25,
  });
  const { data: categoriesData } = useList('categories', endpoints.inventory.categories, { page_size: 200 });
  const categories = categoriesData?.results || categoriesData || [];
  const products = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;
  const activeFilterCount = [search, type, lowStock, categoryId].filter(Boolean).length;

  const clearFilters = () => {
    setSearch('');
    setType('');
    setLowStock(false);
    setCategoryId('');
    setPage(1);
  };

  const columns = [
    { key: 'sku', label: 'SKU', render: (r) => (
      <Link to={`/inventory/products/${r.id}`} className="text-brand-600 font-medium hover:underline">
        {r.sku}
      </Link>
    )},
    { key: 'image', label: 'Image', render: (r) => (
      r.image
        ? <img src={r.image} alt={`${r.name} product`} className="h-10 w-10 rounded object-cover" />
        : <span className="text-xs text-slate-400">No image</span>
    )},
    { key: 'part_number', label: 'Part Number' },
    { key: 'name', label: 'Name' },
    { key: 'category_name', label: 'Category' },
    { key: 'product_type_display', label: 'Type' },
    { key: 'total_quantity', label: 'Stock', align: 'right', render: (r) => (
      <span className={r.needs_reorder ? 'text-red-600 font-semibold' : ''}>
        {Number(r.total_quantity).toFixed(0)}
        {r.needs_reorder && ' ⚠'}
      </span>
    )},
    { key: 'retail_price', label: 'Retail', align: 'right', render: (r) => formatKes(r.retail_price) },
    { key: 'wholesale_price', label: 'Wholesale', align: 'right', render: (r) => formatKes(r.wholesale_price) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Inventory"
        description="Browse products, stock levels, and reorder needs."
        actions={<div className="flex flex-wrap gap-2">
          <Link to="/inventory/products/new" className="btn-primary">+ Product</Link>
        </div>}
      />

      <Filter
        title="Product filters"
        activeCount={activeFilterCount}
        onClear={clearFilters}
        showClear
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4 md:items-end">
          <Input
            placeholder="Search SKU, name, barcode..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="md:col-span-2"
          />
          <Select
            label="Category"
            value={categoryId}
            onChange={(value) => setCategoryId(value)}
            searchable
            options={[
              { value: '', label: 'All categories' },
              ...categories.map((category) => ({ value: category.id, label: category.name })),
            ]}
          />
          <Select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">All types</option>
            <option value="MOTORBIKE_PART">Motorbike Part</option>
            <option value="AUTO_PART">Auto Part</option>
            <option value="ACCESSORY">Accessory</option>
          </Select>
          <Switch label="Low stock only" checked={lowStock} onChange={(e) => setLowStock(e.target.checked)} />
        </div>
      </Filter>

      <DataTable
        columns={columns}
        rows={products}
        loading={isLoading}
        empty="No products found."
      />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}
