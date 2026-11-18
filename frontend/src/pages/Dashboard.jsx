import { useDashboard, useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import MetricCard from '@/components/cards/MetricCard';
import PanelCard from '@/components/cards/PanelCard';
import ChartPanel from '@/components/charts/ChartPanel';
import TrendChart from '@/components/charts/TrendChart';
import PageHeader from '@/components/ui/PageHeader';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { useAuth } from '@/hooks/useAuth';

export default function Dashboard() {
  const { isBoss } = useAuth();
  const { data, isLoading, error } = useDashboard({ enabled: isBoss });
  const { data: lowStock } = useList(
    'low-stock',
    endpoints.reporting.lowStock,
    {},
    { enabled: isBoss },
  );

  if (!isBoss) return null;

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[1, 2, 3, 4].map((index) => (
          <SkeletonCard key={index} className="h-32" />
        ))}
      </div>
    );
  }

  if (error) {
    return <div className="card text-red-600">Failed to load dashboard.</div>;
  }

  if (!data) return null;

  const today = data.today;
  const mtd = data.mtd;
  const alerts = data.alerts;
  const trends = data.trends.last_7_days || [];

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description={`As of ${formatDateTime(data.generated_at)}`} />

      {/* Today */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase mb-3">Today</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Sales Revenue" value={formatKes(today.sales_revenue)} accent="brand" />
          <MetricCard label="Gross Profit" value={formatKes(today.gross_profit)} accent="success" />
          <MetricCard label="Expenses" value={formatKes(today.expenses)} accent="warning" />
          <MetricCard label="Net Profit" value={formatKes(today.net_profit)}
                      accent={Number(today.net_profit) >= 0 ? 'success' : 'danger'} />
        </div>
      </section>

      {/* Month-to-date + Alerts */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <PanelCard title="Month to Date" className="lg:col-span-2">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Revenue" value={formatKes(mtd.net_revenue)} />
            <Stat label="Gross Profit" value={formatKes(mtd.gross_profit)} />
            <Stat label="Expenses" value={formatKes(mtd.expenses)} />
            <Stat label="Net Profit" value={formatKes(mtd.net_profit)}
                  positive={Number(mtd.net_profit) >= 0} />
          </div>
        </PanelCard>
        <PanelCard title="Alerts">
          <AlertRow label="Low stock items" count={alerts.low_stock_count} tone="warning" to="/inventory?filter=low-stock" />
          <AlertRow label="eTIMS failures" count={alerts.etims_failed_count} tone="danger" to="/admin/etims" />
          <AlertRow label="Pending preorders" count={alerts.pending_preorders} tone="neutral" to="/preorders" />
          {Number(alerts.overdue_ar_total) > 0 && (
            <AlertRow label="Overdue AR" amount={formatKes(alerts.overdue_ar_total)} tone="danger" to="/reports/customers/aging" />
          )}
        </PanelCard>
      </section>

      {/* Trend */}
      <ChartPanel title="Sales — Last 7 Days" description="Daily revenue">
        <TrendChart
          data={trends}
          xKey="date"
          series={[{ dataKey: 'revenue', name: 'Revenue', color: '#0f766e' }]}
          valueFormatter={formatKes}
        />
      </ChartPanel>

      {/* Position */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard label="Accounts Receivable" value={formatKes(data.position.ar_total)} />
        <MetricCard label="Cash Position Today" value={formatKes(data.position.cash_position_today)} />
        <MetricCard label="Low Stock Items" value={alerts.low_stock_count} />
      </section>
    </div>
  );
}

function Stat({ label, value, positive }) {
  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-lg font-semibold ${positive === false ? 'text-red-600' : 'text-slate-900'}`}>
        {value}
      </div>
    </div>
  );
}

function AlertRow({ label, count, amount, tone = 'neutral', to }) {
  const tones = {
    warning: 'text-amber-700 bg-amber-50',
    danger:  'text-red-700 bg-red-50',
    neutral: 'text-slate-700 bg-slate-50',
  };
  return (
    <a href={to} className={`flex justify-between items-center rounded-lg px-3 py-2 mb-2 text-sm ${tones[tone]}`}>
      <span>{label}</span>
      <span className="font-semibold">{amount ?? count}</span>
    </a>
  );
}