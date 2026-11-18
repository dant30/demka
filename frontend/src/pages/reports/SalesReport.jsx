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

  const { data: summary } = useQuery({
    queryKey: ['sales-summary', params],
    queryFn: async () => (await api.get(endpoints.reporting.salesSummary, { params })).data,
  });
  const { data: daily } = useQuery({
    queryKey: ['sales-daily', params],
    queryFn: async () => (await api.get(endpoints.reporting.salesByDay, { params })).data,
  });
  const { data: topProducts } = useQuery({
    queryKey: ['top-products', params],
    queryFn: async () => (await api.get(endpoints.reporting.topProducts, { params })).data,
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

      {topProducts && (
        <DataTable
          title="Top Products"
          columns={[
            { key: 'name', label: 'Product', render: (row) => <span><span className="font-medium">{row.name}</span><span className="block text-xs text-slate-500">{row.sku}</span></span> },
            { key: 'units_sold', label: 'Units', align: 'right' },
            { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
            { key: 'margin_pct', label: 'Margin %', align: 'right', render: (row) => `${row.margin_pct}%` },
          ]}
          rows={topProducts}
          keyField="product_id"
          caption="Top products by sales"
        />
      )}
    </div>
  );
}

const Card = ({ label, value }) => (
  <div className="card">
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className="text-xl font-bold mt-1">{value}</div>
  </div>
);