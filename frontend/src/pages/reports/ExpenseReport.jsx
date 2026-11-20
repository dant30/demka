import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import DataTable from '@/components/ui/DataTable';
import MetricCard from '@/components/cards/MetricCard';
import ChartPanel from '@/components/charts/ChartPanel';
import TrendChart from '@/components/charts/TrendChart';
import { ReportHeader } from './ReportLayout';

export default function ExpenseReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());
  const reportParams = { ...params, compare: '1' };

  const summary = useQuery({
    queryKey: ['expense-report-summary', reportParams],
    queryFn: async () => (await api.get(endpoints.reporting.expenseSummary, { params: reportParams })).data,
  });
  const categories = useQuery({
    queryKey: ['expense-report-categories', params],
    queryFn: async () => (await api.get(endpoints.reporting.expenseByCategory, { params })).data,
  });
  const locations = useQuery({
    queryKey: ['expense-report-locations', params],
    queryFn: async () => (await api.get(endpoints.reporting.expenseByLocation, { params })).data,
  });
  const trend = useQuery({
    queryKey: ['expense-report-trend'],
    queryFn: async () => (await api.get(endpoints.reporting.expenseTrend, { params: { months: 12 } })).data,
  });

  const summaryData = summary.data;
  const comparisonTotal = Number(summaryData?.comparison?.total || 0);
  const currentTotal = Number(summaryData?.total || 0);
  const difference = currentTotal - comparisonTotal;

  return (
    <div className="space-y-4">
      <ReportHeader title="Expense Analysis" description="Compare spend and inspect category, location, and monthly trends." />

      {summary.isError && <p role="alert" className="text-sm text-red-700">Could not load expense totals.</p>}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          label="Total expenses"
          value={summary.isLoading ? 'Loading...' : formatKes(summaryData?.total)}
          detail={summaryData?.period ? `${summaryData.period.start} to ${summaryData.period.end}` : undefined}
          accent="warning"
        />
        <MetricCard
          label="Expense count"
          value={summary.isLoading ? 'Loading...' : summaryData?.count ?? 0}
          detail={summaryData?.comparison ? `Previous period: ${summaryData.comparison.count}` : 'For the selected period'}
        />
        <MetricCard
          label="Change from previous"
          value={summaryData?.comparison ? formatKes(Math.abs(difference)) : '—'}
          detail={summaryData?.comparison ? (difference > 0 ? 'More than previous period' : difference < 0 ? 'Less than previous period' : 'No change') : 'No comparison available'}
          accent={difference > 0 ? 'danger' : 'success'}
        />
      </div>

      <ChartPanel title="Monthly trend" description="Expense totals for the last 12 months">
        {trend.isError ? (
          <p role="alert" className="text-sm text-red-700">Could not load expense trend.</p>
        ) : (
          <TrendChart
            data={trend.data || []}
            xKey="label"
            type="bar"
            series={[{ dataKey: 'total', name: 'Expenses', color: '#d97706' }]}
            valueFormatter={formatKes}
            height={240}
            loading={trend.isLoading}
          />
        )}
      </ChartPanel>

      <DataTable
        title="Spending by category"
        columns={[
          { key: 'category', label: 'Category' },
          { key: 'count', label: 'Expenses', align: 'right' },
          { key: 'total', label: 'Total', align: 'right', render: (row) => formatKes(row.total) },
        ]}
        rows={Array.isArray(categories.data) ? categories.data : categories.data?.results || []}
        loading={categories.isLoading}
        empty={categories.isError ? 'Could not load category breakdown.' : 'No expenses in this period.'}
        caption="Expenses by category"
      />

      <DataTable
        title="Spending by location"
        columns={[
          { key: 'location', label: 'Location' },
          { key: 'count', label: 'Expenses', align: 'right' },
          { key: 'total', label: 'Total', align: 'right', render: (row) => formatKes(row.total) },
        ]}
        rows={Array.isArray(locations.data) ? locations.data : locations.data?.results || []}
        loading={locations.isLoading}
        empty={locations.isError ? 'Could not load location breakdown.' : 'No expenses in this period.'}
        caption="Expenses by location"
      />
    </div>
  );
}