import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Pagination from '@/components/ui/Pagination';
import Switch from '@/components/ui/Switch';
import Filter from '@/components/ui/Filter';
import ProductGrid from '@/components/pos/ProductGrid';

export default function InventoryHome() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [lowStock, setLowStock] = useState(false);
  const [categoryId, setCategoryId] = useState('');

  const { data } = useList('products', endpoints.inventory.products, {
    page, search: search || undefined, product_type: type || undefined,
    category: categoryId || undefined, needs_reorder: lowStock || undefined, page_size: 25,
  });
  const { data: categoriesData } = useList('categories', endpoints.inventory.categories, { page_size: 200 });
  const categories = categoriesData?.results || categoriesData || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;
  const activeFilterCount = [type, lowStock, categoryId].filter(Boolean).length;

  const clearFilters = () => {
    setSearch('');
    setType('');
    setLowStock(false);
    setCategoryId('');
    setPage(1);
  };


  return (
    <div className="space-y-4">
      <Filter
        title="Product filters"
        headerContent={(
          <Input
            type="search"
            aria-label="Search products by SKU, name, or barcode"
            placeholder="Search products..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        )}
        activeCount={activeFilterCount}
        onClear={clearFilters}
        showClear
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4 md:items-end">
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

      <ProductGrid
        search={search}
        categoryId={categoryId}
        onSelect={(product) => navigate(`/inventory/products/${product.id}`)}
      />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />
    </div>
  );
}
