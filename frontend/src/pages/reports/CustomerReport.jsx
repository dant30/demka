import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function CustomerReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());
  const agingParams = params.end ? { as_of: params.end } : {};
  const { data: aging } = useQuery({
    queryKey: ['aging', agingParams],
    queryFn: async () => (await api.get(endpoints.reporting.agingSummary, { params: agingParams })).data,
  });
  const { data: agingDetail, isLoading: agingDetailLoading, isError: agingDetailError } = useQuery({
    queryKey: ['aging-detail', agingParams],
    queryFn: async () => (await api.get(endpoints.reporting.agingDetail, { params: agingParams })).data,
  });
  const { data: credit } = useQuery({
    queryKey: ['credit-util'],
    queryFn: async () => (await api.get(endpoints.reporting.creditUtilization)).data,
  });
  const { data: topCustomers, isLoading: topCustomersLoading, isError: topCustomersError } = useQuery({
    queryKey: ['top-customers', params],
    queryFn: async () => (await api.get(endpoints.reporting.topCustomers, { params })).data,
  });

  return (
    <div className="space-y-4">
      <ReportHeader title="Customer Report" description="Receivables and credit" />

      {aging && (
        <>
          <div className="card">
            <div className="text-xs text-slate-500 uppercase">Total Outstanding</div>
            <div className="text-3xl font-bold mt-1">{formatKes(aging.total_outstanding)}</div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(aging.buckets).map(([bucket, amt]) => (
              <div key={bucket} className="card">
                <div className="text-xs text-slate-500 uppercase">{bucket} days</div>
                <div className="text-xl font-semibold mt-1">{formatKes(amt)}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {credit && credit.length > 0 && (
        <DataTable
          title="Credit Utilization"
          columns={[
            { key: 'name', label: 'Customer', render: (row) => <span>{row.name} <span className="text-xs text-slate-500">{row.code}</span></span> },
            { key: 'credit_limit', label: 'Limit', align: 'right', render: (row) => formatKes(row.credit_limit) },
            { key: 'current_balance', label: 'Balance', align: 'right', render: (row) => formatKes(row.current_balance) },
            { key: 'utilization_pct', label: 'Util %', align: 'right', render: (row) => <span className={row.at_limit ? 'font-semibold text-red-600' : ''}>{row.utilization_pct}%</span> },
          ]}
          rows={credit}
          keyField="customer_id"
          caption="Customer credit utilization"
        />
      )}

      <DataTable
        title="Top Customers"
        columns={[
          { key: 'name', label: 'Customer', render: (row) => <span><span className="font-medium">{row.name}</span><span className="block text-xs text-slate-500">{row.code} · {row.customer_type}</span></span> },
          { key: 'sale_count', label: 'Sales', align: 'right' },
          { key: 'revenue', label: 'Revenue', align: 'right', render: (row) => formatKes(row.revenue) },
          { key: 'gross_profit', label: 'Gross Profit', align: 'right', render: (row) => formatKes(row.gross_profit) },
        ]}
        rows={topCustomers || []}
        keyField="customer_id"
        loading={topCustomersLoading}
        empty={topCustomersError ? 'Could not load this report.' : 'No customer sales in this period.'}
        caption="Top customers by revenue"
      />

      <DataTable
        title="Receivables Detail"
        columns={[
          { key: 'sale_number', label: 'Sale', render: (row) => <span><span className="font-medium">{row.sale_number}</span><span className="block text-xs text-slate-500">{row.customer_name} · {row.customer_code}</span></span> },
          { key: 'due_date', label: 'Due Date' },
          { key: 'days_outstanding', label: 'Days', align: 'right' },
          { key: 'bucket', label: 'Age' },
          { key: 'balance_due', label: 'Balance', align: 'right', render: (row) => formatKes(row.balance_due) },
        ]}
        rows={agingDetail || []}
        keyField="sale_number"
        loading={agingDetailLoading}
        empty={agingDetailError ? 'Could not load this report.' : 'No outstanding receivables.'}
        caption="Receivables aging detail"
      />
    </div>
  );
}