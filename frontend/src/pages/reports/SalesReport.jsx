import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import ChartPanel from '@/components/charts/ChartPanel';
import TrendChart from '@/components/charts/TrendChart';
import DataTable from '@/components/ui/DataTable';

export default function SalesReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());

  const { data: summary, isLoading: summaryLoading, isError: summaryError } = useQuery({
    queryKey: ['sales-summary', params],
    queryFn: async () => (await api.get(endpoints.reporting.salesSummary, { params })).data,
  });
  const { data: daily, isLoading: dailyLoading, isError: dailyError } = useQuery({
    queryKey: ['sales-daily', params],
    queryFn: async () => (await api.get(endpoints.reporting.salesByDay, { params })).data,
  });
  const { data: topProducts, isLoading: topProductsLoading, isError: topProductsError } = useQuery({
    queryKey: ['top-products', params],
    queryFn: async () => (await api.get(endpoints.reporting.topProducts, { params })).data,
  });
  const { data: customerTypes, isLoading: customerTypesLoading, isError: customerTypesError } = useQuery({
    queryKey: ['sales-by-customer-type', params],
    queryFn: async () => (await api.get(endpoints.reporting.salesByCustomerType, { params })).data,
  });
  const { data: worstProducts, isLoading: worstProductsLoading, isError: worstProductsError } = useQuery({
    queryKey: ['worst-products', params],
    queryFn: async () => (await api.get(endpoints.reporting.worstProducts, { params })).data,
  });
  const { data: marginAnalysis, isLoading: marginLoading, isError: marginError } = useQuery({
    queryKey: ['margin-analysis', params],
    queryFn: async () => (await api.get(endpoints.reporting.marginAnalysis, { params })).data,
  });

  return (
    <div className="space-y-4">
      <ReportHeader title="Sales Analysis" description="Volume, revenue, and product performance" />

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Card label="Total Revenue" value={formatKes(summary.total_revenue)} />
          <Card label="Sale Count" value={summary.sale_count} />
          <Card label="Cash Revenue" value={formatKes(summary.cash_revenue)} />
        </div>
      )}
      {summaryError && <p className="text-sm text-red-600" role="alert">Could not load sales totals.</p>}

      {daily && (
        <ChartPanel title="Daily Revenue" description="Sales revenue over the selected period">
          <TrendChart
            data={daily}
            xKey="date"
            series={[{ dataKey: 'revenue', name: 'Revenue', color: '#0f766e' }]}
            valueFormatter={formatKes}
          />
        </ChartPanel>
      )}
      {dailyError && <p className="text-sm text-red-600" role="alert">Could not load daily revenue.</p>}

      <DataTable
        title="Top Products"
        columns={[
          { key: 'name', label: 'Product', render: (row) => <span><span className="font-medium">{row.name}</span><span className="block text-xs text-slate-500">{row.sku}</span></span> },
          { key: 'units_sold', label: 'Units', align: 'right' },
          { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
          { key: 'margin_pct', label: 'Margin %', align: 'right', render: (row) => `${row.margin_pct}%` },
        ]}
        rows={topProducts || []}
        keyField="product_id"
        loading={topProductsLoading}
        empty={topProductsError ? 'Could not load this report.' : 'No product sales in this period.'}
        caption="Top products by sales"
      />

      <DataTable
        title="Sales by Customer Type"
        columns={[
          { key: 'customer_type', label: 'Customer Type' },
          { key: 'count', label: 'Sales', align: 'right' },
          { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
        ]}
        rows={customerTypes || []}
        keyField="customer_type"
        loading={customerTypesLoading}
        empty={customerTypesError ? 'Could not load this report.' : 'No sales in this period.'}
        caption="Sales by customer type"
      />

      <DataTable
        title="Lowest Revenue Products"
        columns={[
          { key: 'name', label: 'Product', render: (row) => <span><span className="font-medium">{row.name}</span><span className="block text-xs text-slate-500">{row.sku}</span></span> },
          { key: 'units_sold', label: 'Units', align: 'right' },
          { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
          { key: 'gross_profit', label: 'Gross Profit', align: 'right', render: (row) => formatKes(row.gross_profit) },
        ]}
        rows={worstProducts || []}
        keyField="product_id"
        loading={worstProductsLoading}
        empty={worstProductsError ? 'Could not load this report.' : 'No product sales in this period.'}
        caption="Lowest revenue products"
      />

      <DataTable
        title="Product Margin Analysis"
        columns={[
          { key: 'name', label: 'Product', render: (row) => <span><span className="font-medium">{row.name}</span><span className="block text-xs text-slate-500">{row.sku}</span></span> },
          { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
          { key: 'cogs', label: 'Cost', align: 'right', render: (row) => formatKes(row.cogs) },
          { key: 'gross_profit', label: 'Gross Profit', align: 'right', render: (row) => formatKes(row.gross_profit) },
          { key: 'margin_pct', label: 'Margin %', align: 'right', render: (row) => `${row.margin_pct}%` },
        ]}
        rows={marginAnalysis || []}
        keyField="product_id"
        loading={marginLoading}
        empty={marginError ? 'Could not load this report.' : 'No products meet the margin report minimum.'}
        caption="Product margin analysis"
      />
    </div>
  );
}

const Card = ({ label, value }) => (
  <div className="card">
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className="text-xl font-bold mt-1">{value}</div>
  </div>
);