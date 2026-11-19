import { useSearchParams } from 'react-router-dom';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';
import Select from '@/components/ui/Select';

export default function SupplierReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());
  const [productId, setProductId] = useState('');
  const [months, setMonths] = useState('6');
  const { data: productsData, isLoading: productsLoading } = useList(
    'supplier-price-trend-products', endpoints.inventory.products, { page_size: 500 }
  );
  const products = productsData?.results || productsData || [];

  const { data } = useQuery({
    queryKey: ['supplier-purchases', params],
    queryFn: async () => (await api.get(endpoints.reporting.purchasesBySupplier, { params })).data,
  });
  const priceTrend = useQuery({
    queryKey: ['supplier-price-trend', productId, months],
    queryFn: async () => (await api.get(endpoints.reporting.supplierPriceTrend, {
      params: { product: productId, months },
    })).data,
    enabled: Boolean(productId),
  });

  return (
    <div className="space-y-4">
      <ReportHeader title="Supplier Report" description="Purchase spend by supplier" />
      <DataTable
        title="Purchases by Supplier"
        columns={[
          { key: 'name', label: 'Supplier', render: (row) => <span><span className="font-medium">{row.name}</span><span className="block text-xs text-slate-500">{row.code}</span></span> },
          { key: 'po_count', label: 'PO Count', align: 'right' },
          { key: 'total_spent', label: 'Total Spend', align: 'right', render: (row) => formatKes(row.total_spent) },
        ]}
        rows={data || []}
        keyField="supplier_id"
        empty="No supplier purchases in this period."
        caption="Supplier purchases report"
      />

      <section className="space-y-3">
        <div>
          <h2 className="text-base font-semibold">Purchase Price Trend</h2>
          <p className="text-sm text-slate-500">Compare received unit costs over time.</p>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Select
            label="Product"
            value={productId}
            onChange={setProductId}
            disabled={productsLoading}
            searchable
            placeholder={productsLoading ? 'Loading products...' : 'Select a product'}
            options={[
              { value: '', label: 'Select a product...' },
              ...products.map((product) => ({
                value: product.id,
                label: product.name,
                sublabel: product.sku,
              })),
            ]}
          />
          <Select
            label="History"
            value={months}
            onChange={setMonths}
            options={[
              { value: '3', label: 'Last 3 months' },
              { value: '6', label: 'Last 6 months' },
              { value: '12', label: 'Last 12 months' },
              { value: '24', label: 'Last 24 months' },
            ]}
          />
        </div>
        {productId ? (
          <DataTable
            title="Received Unit Costs"
            columns={[
              { key: 'month', label: 'Month' },
              { key: 'total_qty', label: 'Quantity Received', align: 'right' },
              { key: 'total_cost', label: 'Total Cost', align: 'right', render: (row) => formatKes(row.total_cost) },
              { key: 'avg_unit_cost', label: 'Average Unit Cost', align: 'right', render: (row) => formatKes(row.avg_unit_cost) },
            ]}
            rows={priceTrend.data || []}
            loading={priceTrend.isLoading}
            empty={priceTrend.isError ? 'Could not load this report.' : 'No received goods for this product in the selected history.'}
            caption="Supplier received price trend"
          />
        ) : (
          <p className="rounded-md border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
            Select a product to view its received price history.
          </p>
        )}
      </section>
    </div>
  );
}