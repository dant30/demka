import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function StockReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());

  const valuationQuery = useQuery({
    queryKey: ['stock-valuation', params],
    queryFn: async () => (await api.get(endpoints.reporting.stockValuation, { params })).data,
  });
  const lowStockQuery = useQuery({
    queryKey: ['stock-low-stock'],
    queryFn: async () => (await api.get(endpoints.reporting.lowStock)).data,
  });
  const movementsQuery = useQuery({
    queryKey: ['stock-movements', params],
    queryFn: async () => (await api.get(endpoints.reporting.stockMovements, { params })).data,
  });
  const deadStockQuery = useQuery({
    queryKey: ['stock-dead-stock'],
    queryFn: async () => (await api.get(endpoints.reporting.deadStock)).data,
  });

  const valuation = valuationQuery.data;
  const lowStock = lowStockQuery.data;
  const movements = movementsQuery.data;
  const deadStock = deadStockQuery.data;

  return (
    <div className="space-y-4">
      <ReportHeader title="Stock Report" description="Valuation, low stock, movements, and dead stock" />

      {valuation && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Summary label="As of" value={valuation.as_of || '—'} />
          <Summary label="Total units" value={valuation.total_units ?? '—'} />
          <Summary label="Stock value" value={formatKes(valuation.total_value)} />
        </div>
      )}

      <DataTable
        title="Valuation by Location"
        caption="Stock valuation by location"
        loading={valuationQuery.isLoading}
        empty={valuationQuery.isError ? 'Could not load this report.' : 'No data available.'}
        columns={[
          { key: 'location_name', label: 'Location' },
          { key: 'total_units', label: 'Units', align: 'right' },
          { key: 'total_value', label: 'Value', align: 'right', render: (row) => formatKes(row.total_value) },
        ]}
        rows={valuation?.by_location || []}
        keyField="location_id"
      />

      <DataTable
        title="Low Stock"
        caption="Low stock report"
        loading={lowStockQuery.isLoading}
        empty={lowStockQuery.isError ? 'Could not load this report.' : 'No data available.'}
        columns={[
          { key: 'sku', label: 'SKU' },
          { key: 'name', label: 'Product' },
          { key: 'location_name', label: 'Location' },
          { key: 'quantity', label: 'Quantity', align: 'right' },
          { key: 'reorder_level', label: 'Reorder at', align: 'right' },
          { key: 'suggested_qty', label: 'Suggested', align: 'right' },
        ]}
        rows={lowStock || []}
        keyField="product_id"
      />

      <DataTable
        title="Stock Movements"
        caption="Stock movement report"
        loading={movementsQuery.isLoading}
        empty={movementsQuery.isError ? 'Could not load this report.' : 'No data available.'}
        columns={[
          { key: 'movement_type', label: 'Movement', render: (row) => row.movement_type.replaceAll('_', ' ') },
          { key: 'count', label: 'Count', align: 'right' },
          { key: 'net_units', label: 'Net units', align: 'right' },
        ]}
        rows={movements?.by_type || []}
        keyField="movement_type"
      />

      <DataTable
        title="Dead Stock"
        caption="Dead stock report"
        loading={deadStockQuery.isLoading}
        empty={deadStockQuery.isError ? 'Could not load this report.' : 'No data available.'}
        columns={[
          { key: 'sku', label: 'SKU' },
          { key: 'name', label: 'Product' },
          { key: 'brand', label: 'Brand', render: (row) => row.brand || '—' },
          { key: 'total_quantity', label: 'Quantity', align: 'right' },
          { key: 'stock_value', label: 'Stock value', align: 'right', render: (row) => formatKes(row.stock_value) },
        ]}
        rows={deadStock || []}
        keyField="product_id"
      />
    </div>
  );
}

function Summary({ label, value }) {
  return (
    <div className="card">
      <div className="text-xs text-slate-500 uppercase">{label}</div>
      <div className="mt-1 font-semibold">{value}</div>
    </div>
  );
}

