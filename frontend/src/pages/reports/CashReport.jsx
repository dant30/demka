import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function CashReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());

  const { data: daily } = useQuery({
    queryKey: ['cash-daily', params],
    queryFn: async () => (await api.get(endpoints.reporting.cashReconciliation, { params })).data,
  });
  const { data: methods } = useQuery({
    queryKey: ['payment-methods-report', params],
    queryFn: async () => (await api.get(endpoints.reporting.paymentMethods, { params })).data,
  });
  const variance = useQuery({
    queryKey: ['cash-variance-report', params],
    queryFn: async () => (await api.get(endpoints.reporting.cashVariance, { params })).data,
  });

  return (
    <div className="space-y-4">
      <ReportHeader title="Cash & Payments" description="Daily reconciliation and method breakdown" />

      {methods && (
        <DataTable
          title="Payment Methods"
          columns={[
            { key: 'method_name', label: 'Method' },
            { key: 'count', label: 'Count', align: 'right' },
            { key: 'total', label: 'Total', align: 'right', render: (row) => formatKes(row.total) },
          ]}
          rows={methods}
          keyField="method_code"
          caption="Payment methods report"
        />
      )}

      {daily && (
        <DataTable
          title="Daily Reconciliation"
          columns={[
            { key: 'date', label: 'Date' },
            { key: 'collected', label: 'Collected', align: 'right', render: (row) => formatKes(row.collected) },
            { key: 'spent', label: 'Spent', align: 'right', render: (row) => formatKes(row.spent) },
            { key: 'expected', label: 'Expected', align: 'right', render: (row) => formatKes(row.expected) },
          ]}
          rows={daily}
          keyField="date"
          caption="Daily cash reconciliation"
        />
      )}

      <DataTable
        title="Field Run Cash Variance"
        columns={[
          { key: 'run_date', label: 'Date', render: (row) => <span><span className="font-medium">{row.run_date}</span><span className="block text-xs text-slate-500">{row.route.code} · {row.route.name}</span></span> },
          { key: 'agent', label: 'Agent', render: (row) => row.agent.name },
          { key: 'cash_expected', label: 'Expected', align: 'right', render: (row) => formatKes(row.cash_expected) },
          { key: 'cash_handed_in', label: 'Handed In', align: 'right', render: (row) => formatKes(row.cash_handed_in) },
          { key: 'variance', label: 'Variance', align: 'right', render: (row) => <span className={Number(row.variance) === 0 ? '' : 'font-semibold text-red-600'}>{formatKes(row.variance)}</span> },
        ]}
        rows={variance.data || []}
        keyField="run_id"
        loading={variance.isLoading}
        empty={variance.isError ? 'Could not load this report.' : 'No cash variances in this period.'}
        caption="Field run cash variance"
      />
    </div>
  );
}