import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { PERIODS } from '@/utils/dates';
import { formatKes } from '@/utils/money';
import PageHeader from '@/components/ui/PageHeader';
import Filter from '@/components/ui/Filter';
import Select from '@/components/ui/Select';
import MetricCard from '@/components/cards/MetricCard';

export default function RoutePerformanceReport() {
  const [searchParams, setSearchParams] = useSearchParams();
  const agentId = searchParams.get('agent') || '';
  const period = searchParams.get('period') || 'monthly';

  const { data: agentData, isLoading: agentsLoading, isError: agentsError } = useQuery({
    queryKey: ['field-performance-agents'],
    queryFn: async () => (await api.get(endpoints.users.list, {
      params: { is_active: true, page_size: 200 },
    })).data,
  });
  const agents = (agentData?.results || agentData || []).filter(
    (agent) => agent.role === 'FIELD_AGENT',
  );

  const report = useQuery({
    queryKey: ['agent-performance', agentId, period],
    queryFn: async () => (await api.get(endpoints.routes.agentPerformance, {
      params: { agent: agentId, period },
    })).data,
    enabled: Boolean(agentId),
  });

  const setParam = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Field Performance"
        description="Route-run activity, sales, and cash variance by agent."
      />

      <Filter title="Report filters">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Select
            aria-label="Field agent"
            className="w-full"
            value={agentId}
            disabled={agentsLoading || agentsError}
            onChange={(event) => setParam('agent', event.target.value)}
          >
            <option value="">Select a field agent</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.full_name || agent.username}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Report period"
            className="w-full"
            value={period}
            onChange={(event) => setParam('period', event.target.value)}
          >
            {PERIODS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </Select>
        </div>
      </Filter>

      {agentsError && (
        <p role="alert" className="text-sm text-red-700">Could not load field agents.</p>
      )}
      {report.isError && (
        <p role="alert" className="text-sm text-red-700">Could not load this report.</p>
      )}
      {!agentId && !agentsError && (
        <p className="py-8 text-center text-sm text-slate-500">Select an agent to view performance.</p>
      )}
      {agentId && report.isLoading && (
        <p className="py-8 text-center text-sm text-slate-500" role="status">Loading performance...</p>
      )}
      {report.data && (
        <>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-base font-semibold text-slate-900">{report.data.agent.name}</h2>
            <p className="text-sm text-slate-500">
              {report.data.period.start} to {report.data.period.end}
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Field sales" value={formatKes(report.data.sales_total)} />
            <MetricCard label="Runs" value={report.data.runs.total} detail="Total in period" />
            <MetricCard label="Completed runs" value={report.data.runs.completed} detail="Closed route runs" accent="success" />
            <MetricCard
              label="Cash variance"
              value={formatKes(report.data.cash_variance.total)}
              detail={`Average per completed run: ${formatKes(report.data.cash_variance.average)}`}
              accent={Number(report.data.cash_variance.total) === 0 ? 'success' : 'warning'}
            />
          </div>
        </>
      )}
    </div>
  );
}