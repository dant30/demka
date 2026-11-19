import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function ProfitLossReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());

  const { data, isLoading } = useQuery({
    queryKey: ['report-pl', params],
    queryFn: async () => (await api.get(endpoints.reporting.profitLoss, { params })).data,
  });
  const channelReport = useQuery({
    queryKey: ['profit-by-channel', params],
    queryFn: async () => (await api.get(endpoints.reporting.profitByChannel, { params })).data,
  });
  const productTypeReport = useQuery({
    queryKey: ['profit-by-product-type', params],
    queryFn: async () => (await api.get(endpoints.reporting.profitByProductType, { params })).data,
  });

  if (isLoading) return <div>Loading...</div>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <ReportHeader title="Profit & Loss" description="Revenue, costs, and profitability" />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card label="Net Revenue" value={formatKes(data.revenue.net)} />
        <Card label="COGS" value={formatKes(data.cogs.net)} />
        <Card label="Gross Profit" value={formatKes(data.gross_profit)} accent="success" />
        <Card label="Net Profit" value={formatKes(data.net_profit)} accent={Number(data.net_profit) >= 0 ? 'success' : 'danger'} />
      </div>

      <div className="card">
        <h3 className="font-semibold mb-3">Breakdown</h3>
        <div className="space-y-2">
          <Row label="Gross Revenue" value={formatKes(data.revenue.gross)} />
          <Row label="Less Refunds" value={`(${formatKes(data.revenue.refunds)})`} />
          <Row label="Net Revenue" value={formatKes(data.revenue.net)} bold />
          <Row label="COGS" value={`(${formatKes(data.cogs.net)})`} />
          <Row label="Gross Profit" value={formatKes(data.gross_profit)} bold />
          <Row label={`Gross Margin (${data.gross_margin_pct}%)`} value="" />
          <Row label="Operating Expenses" value={`(${formatKes(data.expenses)})`} />
          <Row label="Net Profit" value={formatKes(data.net_profit)} bold accent />
          <Row label={`Net Margin (${data.net_margin_pct}%)`} value="" />
        </div>
      </div>

      {data.comparison && (
        <div className="card">
          <h3 className="font-semibold mb-3">vs. Previous Period</h3>
          <div className="space-y-1">
            <Row label="Revenue Change" value={`${data.comparison.revenue_change_pct}%`} />
            <Row label="Gross Profit Change" value={`${data.comparison.gross_profit_change_pct}%`} />
            <Row label="Net Profit Change" value={`${data.comparison.net_profit_change_pct}%`} />
          </div>
        </div>
      )}

      <DataTable
        title="Profit by Sales Channel"
        columns={[
          { key: 'channel', label: 'Channel' },
          { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
          { key: 'cogs', label: 'Cost of Goods', align: 'right', render: (row) => formatKes(row.cogs) },
          { key: 'gross_profit', label: 'Gross Profit', align: 'right', render: (row) => formatKes(row.gross_profit) },
          { key: 'margin_pct', label: 'Margin %', align: 'right', render: (row) => `${row.margin_pct}%` },
        ]}
        rows={channelReport.data || []}
        loading={channelReport.isLoading}
        empty={channelReport.isError ? 'Could not load this report.' : 'No sales in this period.'}
        caption="Profit by sales channel"
      />

      <DataTable
        title="Profit by Product Type"
        columns={[
          { key: 'product_type', label: 'Product Type' },
          { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
          { key: 'cogs', label: 'Cost of Goods', align: 'right', render: (row) => formatKes(row.cogs) },
          { key: 'gross_profit', label: 'Gross Profit', align: 'right', render: (row) => formatKes(row.gross_profit) },
          { key: 'margin_pct', label: 'Margin %', align: 'right', render: (row) => `${row.margin_pct}%` },
        ]}
        rows={productTypeReport.data || []}
        loading={productTypeReport.isLoading}
        empty={productTypeReport.isError ? 'Could not load this report.' : 'No product sales in this period.'}
        caption="Profit by product type"
      />
    </div>
  );
}

const Card = ({ label, value, accent }) => {
  const tones = { success: 'border-green-200 bg-green-50', danger: 'border-red-200 bg-red-50' };
  return (
    <div className={`card ${accent ? tones[accent] : ''}`}>
      <div className="text-xs text-slate-500 uppercase">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
};
const Row = ({ label, value, bold, accent }) => (
  <div className={`flex justify-between ${bold ? 'font-semibold text-lg pt-2 border-t' : ''} ${accent ? 'text-brand-700' : ''}`}>
    <span>{label}</span><span>{value}</span>
  </div>
);