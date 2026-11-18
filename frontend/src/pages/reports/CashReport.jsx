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
    </div>
  );
}