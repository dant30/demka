import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDashboard, useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes, formatNumber } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import MetricCard from '@/components/cards/MetricCard';
import PanelCard from '@/components/cards/PanelCard';
import ChartPanel from '@/components/charts/ChartPanel';
import TrendChart from '@/components/charts/TrendChart';
import CircularProgress from '@/components/ui/CircularProgress';
import PageHeader from '@/components/ui/PageHeader';
import Select from '@/components/ui/Select';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { useAuth } from '@/hooks/useAuth';

const toNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

function getList(data) {
  if (Array.isArray(data?.results)) return data.results;
  if (Array.isArray(data)) return data;
  return [];
}

function DashboardSkeleton() {
  return (
    <div className="space-y-5 animate-pulse">
      <div>
        <div className="h-7 w-40 rounded bg-slate-200 dark:bg-slate-800" />
        <div className="mt-2 h-4 w-52 rounded bg-slate-100 dark:bg-slate-800" />
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[1, 2, 3, 4].map((index) => <SkeletonCard key={index} className="h-28" />)}
      </div>
      <div className="h-56 rounded-2xl bg-slate-100 dark:bg-slate-800" />
      <div className="h-64 rounded-2xl bg-slate-100 dark:bg-slate-800" />
    </div>
  );
}

function SectionHeading({ title, description }) {
  return (
    <div className="mb-3">
      <h2 className="text-sm font-bold text-slate-900 dark:text-white">{title}</h2>
      {description && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{description}</p>}
    </div>
  );
}

function Stat({ label, value, positive }) {
  return (
    <div className="min-w-0">
      <div className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</div>
      <div className={`mt-1 break-words text-base font-bold tabular-nums sm:text-lg ${positive === true ? 'text-emerald-600 dark:text-emerald-400' : positive === false ? 'text-red-600 dark:text-red-400' : 'text-slate-900 dark:text-white'}`}>
        {value}
      </div>
    </div>
  );
}

function AlertRow({ label, count, amount, tone = 'neutral', to }) {
  const tones = {
    warning: 'border-amber-200 bg-amber-50/70 text-amber-800 hover:bg-amber-100 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300',
    danger: 'border-red-200 bg-red-50/70 text-red-800 hover:bg-red-100 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-300',
    neutral: 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-800/40 dark:text-slate-200',
  };

  return (
    <Link to={to} className={`mb-2 flex min-w-0 items-center justify-between gap-3 rounded-xl border px-3 py-2.5 text-sm transition-colors ${tones[tone]}`}>
      <span className="truncate text-xs font-medium sm:text-sm">{label}</span>
      <span className="shrink-0 font-bold tabular-nums">{amount ?? count ?? 0}</span>
    </Link>
  );
}

function LowStockWatchlist({ items, loading, totalCount }) {
  const visibleItems = items.slice(0, 5);

  return (
    <PanelCard title="Inventory watchlist" description="Products requiring attention">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-lg font-bold text-slate-900 dark:text-white">
          {formatNumber(totalCount, 0)} <span className="text-xs font-medium text-slate-500">items</span>
        </p>
        <Link to="/inventory?filter=low-stock" className="text-xs font-semibold text-brand-600 dark:text-brand-400">View all</Link>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((item) => <div key={item} className="h-14 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />)}
        </div>
      ) : visibleItems.length ? (
        <div className="space-y-2">
          {visibleItems.map((item, index) => {
            const name = item.product_name || item.name || item.product?.name || 'Unnamed product';
            const sku = item.sku || item.product?.sku || 'No SKU';
            const quantity = toNumber(item.quantity ?? item.total_quantity ?? item.current_quantity ?? item.stock_quantity);
            const reorder = toNumber(item.reorder_level ?? item.product?.reorder_level);
            return (
              <Link key={item.id || item.product_id || `${name}-${index}`} to={`/inventory/products/${item.product_id || item.id}`} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 p-3 hover:border-brand-200 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/40">
                <div className="min-w-0">
                  <p className="truncate text-xs font-semibold text-slate-900 dark:text-white sm:text-sm">{name}</p>
                  <p className="mt-1 truncate text-[11px] text-slate-500 dark:text-slate-400">{sku}</p>
                </div>
                <div className="shrink-0 text-right">
                  <p className={`text-sm font-bold ${quantity <= 0 ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'}`}>{formatNumber(quantity, 0)}</p>
                  <p className="text-[10px] text-slate-500">Reorder: {formatNumber(reorder, 0)}</p>
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-200 px-4 py-8 text-center dark:border-slate-700">
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">Inventory looks good</p>
          <p className="mt-1 text-xs text-slate-500">No low-stock products were returned.</p>
        </div>
      )}
    </PanelCard>
  );
}

export default function Dashboard() {
  const { isBoss } = useAuth();
  const [period, setPeriod] = useState('monthly');
  const dashboardParams = { period };
  const { data, isLoading, error } = useDashboard({ params: dashboardParams, enabled: isBoss });
  const { data: lowStock, isLoading: lowStockLoading, isError: lowStockError } = useList('low-stock', endpoints.reporting.lowStock, {}, { enabled: isBoss });

  if (!isBoss) return null;
  if (isLoading && !data) return <DashboardSkeleton />;
  if (error && !data) {
    return (
      <div className="flex min-h-[280px] flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50/50 p-6 text-center dark:border-red-900/50 dark:bg-red-950/20">
        <p className="text-base font-bold text-red-700 dark:text-red-400">Dashboard unavailable</p>
        <p className="mt-1 text-sm text-slate-500">Business information could not be retrieved.</p>
      </div>
    );
  }
  if (!data) return null;

  const today = data.today || {};
  const mtd = data.mtd || {};
  const alerts = data.alerts || {};
  const position = data.position || {};
  const trends = data.trends?.period || data.trends?.last_7_days || [];
  const lowStockItems = getList(lowStock);
  const lowStockCount = toNumber(alerts.low_stock_count);
  const lowStockTotal = lowStock?.count ?? lowStockCount;

  const mtdRevenue = toNumber(mtd.net_revenue);
  const mtdGrossProfit = toNumber(mtd.gross_profit);
  const grossMargin = mtdRevenue > 0 ? (mtdGrossProfit / mtdRevenue) * 100 : 0;
  const grossMarginProgress = Math.min(100, Math.max(0, grossMargin));

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-5 pb-8">
      <PageHeader
        title="Dashboard"
        description={data.generated_at ? `As of ${formatDateTime(data.generated_at)}` : 'Your business performance at a glance.'}
        actions={(
          <Select
            value={period}
            onChange={setPeriod}
            options={[
              { value: 'daily', label: 'Today' },
              { value: 'yesterday', label: 'Yesterday' },
              { value: 'weekly', label: 'Last 7 days' },
              { value: 'monthly', label: 'This month' },
              { value: 'quarterly', label: 'This quarter' },
              { value: 'yearly', label: 'This year' },
            ]}
            placeholder="Select period"
            className="w-40"
            aria-label="Date range"
          />
        )}
      />

      {error && data && (
        <div role="status" className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300">
          Latest figures could not refresh. Showing the last available data.
        </div>
      )}

      <section>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <MetricCard label="Sales Revenue" value={formatKes(today.sales_revenue)} accent="brand" />
          <MetricCard label="Gross Profit" value={formatKes(today.gross_profit)} accent="success" />
          <MetricCard label="Expenses" value={formatKes(today.expenses)} accent="warning" />
          <MetricCard label="Net Profit" value={formatKes(today.net_profit)} accent={toNumber(today.net_profit) >= 0 ? 'success' : 'danger'} />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <PanelCard title="Month-to-date performance">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
              <div className="grid grid-cols-2 gap-x-4 gap-y-5">
                <Stat label="Revenue" value={formatKes(mtd.net_revenue)} />
                <Stat label="Gross profit" value={formatKes(mtd.gross_profit)} positive={mtdGrossProfit >= 0} />
                <Stat label="Expenses" value={formatKes(mtd.expenses)} />
                <Stat label="Net profit" value={formatKes(mtd.net_profit)} positive={toNumber(mtd.net_profit) >= 0} />
              </div>
              {mtdRevenue > 0 ? (
                <CircularProgress value={grossMarginProgress} max={100} size="lg" variant={grossMargin < 0 ? 'danger' : 'success'} label="Gross margin" valueLabel={`${grossMargin.toFixed(1)}%`} description="Gross profit / revenue" className="justify-self-center" />
              ) : (
                <div className="py-4 text-center sm:px-4"><p className="text-2xl font-bold text-slate-400">—</p><p className="text-xs font-medium text-slate-500">No revenue recorded</p></div>
              )}
            </div>
          </PanelCard>
        </div>

        <div className="min-w-0">
          <PanelCard title="Business alerts">
            <AlertRow label="Low stock items" count={lowStockCount} tone="warning" to="/inventory?filter=low-stock" />
            <AlertRow label="eTIMS failures" count={alerts.etims_failed_count} tone="danger" to="/admin/etims" />
            <AlertRow label="Pending preorders" count={alerts.pending_preorders} tone="neutral" to="/preorders" />
            {toNumber(alerts.overdue_ar_total) > 0 && <AlertRow label="Overdue receivables" amount={formatKes(alerts.overdue_ar_total)} tone="danger" to="/reports/customers/aging" />}
          </PanelCard>
        </div>
      </section>

      <ChartPanel title="Sales performance" description="Daily revenue for the selected period">
        {trends.length ? <TrendChart data={trends} xKey="date" series={[{ dataKey: 'revenue', name: 'Revenue', color: '#0f766e' }]} valueFormatter={formatKes} /> : (
          <div className="flex min-h-56 items-center justify-center text-center"><div><p className="text-sm font-semibold text-slate-800 dark:text-slate-200">No sales trend available</p><p className="mt-1 text-xs text-slate-500">Sales data will appear when transactions are recorded.</p></div></div>
        )}
      </ChartPanel>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <LowStockWatchlist items={lowStockItems} loading={lowStockLoading} totalCount={lowStockTotal} />

        <PanelCard title="Financial position">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/50">
              <p className="text-xs font-medium text-slate-500">Accounts receivable</p>
              <p className="mt-2 break-words text-lg font-bold text-slate-900 dark:text-white">{formatKes(position.ar_total)}</p>
              <Link to="/reports/customers/aging" className="mt-2 inline-block text-xs font-semibold text-brand-600">View receivables</Link>
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/50">
              <p className="text-xs font-medium text-slate-500">Cash position today</p>
              <p className="mt-2 break-words text-lg font-bold text-slate-900 dark:text-white">{formatKes(position.cash_position_today)}</p>
              <p className="mt-2 text-xs text-slate-500">Today's recorded cash position</p>
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-slate-200 p-4 dark:border-slate-700">
            <div className="flex items-center justify-between gap-3">
              <div><p className="text-xs font-medium text-slate-500">Inventory alerts</p><p className="mt-1 text-xl font-bold text-slate-900 dark:text-white">{formatNumber(lowStockCount, 0)}</p></div>
              <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-500/10 dark:text-amber-400">Requires attention</span>
            </div>
            <Link to="/inventory?filter=low-stock" className="mt-3 inline-flex text-xs font-semibold text-brand-600">Review inventory alerts</Link>
          </div>
        </PanelCard>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <PanelCard title="Top-selling products">
          {(data.top_products || []).length ? (
            <div className="space-y-2">
              {data.top_products.map((item) => (
                <Link key={item.product_id} to={`/inventory/products/${item.product_id}`} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 p-3 dark:border-slate-800">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">{item.name}</p>
                    <p className="mt-1 text-[11px] text-slate-500">{item.sku || 'No SKU'} · {formatNumber(item.units_sold, 1)} units</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-sm font-bold text-slate-900 dark:text-white">{formatKes(item.revenue)}</p>
                    <p className="text-[10px] text-emerald-600">Profit {formatKes(item.gross_profit)}</p>
                  </div>
                </Link>
              ))}
            </div>
          ) : <p className="rounded-xl border border-dashed border-slate-200 py-8 text-center text-xs text-slate-500 dark:border-slate-700">No product sales in this period.</p>}
        </PanelCard>

        <PanelCard title="Branch performance">
          {(data.branch_performance || []).length ? (
            <div className="space-y-2">{data.branch_performance.map((branch) => (
              <div key={branch.location_id} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-3 dark:bg-slate-800/50">
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{branch.name}</p>
                  <p className="mt-1 text-[11px] text-slate-500">{branch.sales_count} sales</p>
                </div>
                <p className="text-sm font-bold text-slate-900 dark:text-white">{formatKes(branch.revenue)}</p>
              </div>
            ))}</div>
          ) : <p className="rounded-xl border border-dashed border-slate-200 py-8 text-center text-xs text-slate-500 dark:border-slate-700">No branch sales in this period.</p>}
        </PanelCard>
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Supplier payables" value={formatKes(data.payables?.supplier_outstanding)} accent="warning" />
        <MetricCard label="Inventory valuation" value={formatKes(data.inventory?.valuation)} accent="brand" />
        <MetricCard label="Stock turnover" value={formatNumber(data.inventory?.stock_turnover, 2)} accent="success" />
        <MetricCard label="eTIMS pending" value={formatNumber(data.etims?.pending_count, 0)} accent="warning" />
      </section>

      {lowStockError && <p role="status" className="text-xs text-amber-700 dark:text-amber-400">The inventory watchlist could not be refreshed. The alert count is still available.</p>}
    </div>
  );
}