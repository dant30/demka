import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function CustomerReport() {
  const { data: aging } = useQuery({
    queryKey: ['aging'],
    queryFn: async () => (await api.get(endpoints.reporting.agingSummary)).data,
  });
  const { data: credit } = useQuery({
    queryKey: ['credit-util'],
    queryFn: async () => (await api.get(endpoints.reporting.creditUtilization)).data,
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
    </div>
  );
}