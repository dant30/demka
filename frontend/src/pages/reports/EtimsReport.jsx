import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function EtimsReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());

  const { data: health } = useQuery({
    queryKey: ['etims-health', params],
    queryFn: async () => (await api.get(endpoints.reporting.etimsHealth, { params })).data,
  });
  const { data: failures } = useQuery({
    queryKey: ['etims-failures'],
    queryFn: async () => (await api.get(endpoints.reporting.etimsFailures, { params: { limit: 50 } })).data,
  });

  return (
    <div className="space-y-4">
      <ReportHeader title="eTIMS Health" description="Submission success rates and failures" />

      {health && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card"><div className="text-xs text-slate-500 uppercase">Total</div><div className="text-2xl font-bold">{health.total}</div></div>
          <div className="card"><div className="text-xs text-slate-500 uppercase">Submitted</div><div className="text-2xl font-bold text-green-600">{health.submitted}</div></div>
          <div className="card"><div className="text-xs text-slate-500 uppercase">Failed</div><div className="text-2xl font-bold text-red-600">{health.failed + health.rejected}</div></div>
          <div className="card"><div className="text-xs text-slate-500 uppercase">Success Rate</div><div className="text-2xl font-bold">{health.success_rate_pct}%</div></div>
        </div>
      )}

      {failures && failures.length > 0 && (
        <DataTable
          title="Recent Failures"
          columns={[
            { key: 'invoice_number', label: 'Invoice' },
            { key: 'status', label: 'Status' },
            { key: 'retry_count', label: 'Retries' },
            { key: 'error_message', label: 'Error', render: (row) => <span className="text-xs text-red-600">{row.error_message}</span> },
          ]}
          rows={failures}
          caption="Recent eTIMS submission failures"
        />
      )}
    </div>
  );
}