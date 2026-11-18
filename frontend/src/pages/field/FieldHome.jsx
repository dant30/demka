import { useState } from 'react';
import { Link } from 'react-router-dom';
import { extractError } from '@/api/client';
import { useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { useAuth } from '@/hooks/useAuth';
import { useTodayFieldRuns } from '@/hooks/useTodayFieldRuns';
import { formatDate, todayIso } from '@/utils/dates';
import { formatKes } from '@/utils/money';
import Button from '@/components/ui/Button';

export default function FieldHome() {
  const { user } = useAuth();
  const canManageRuns = user?.role === 'BOSS' || user?.role === 'ADMIN';
  const [materializeMessage, setMaterializeMessage] = useState('');
  const materializeRuns = useAction(
    'field-runs',
    () => endpoints.routes.runMaterialize,
    { invalidate: ['field-runs'] },
  );

  const { isLoading, activeRuns, plannedRuns: planned } = useTodayFieldRuns(user);

  const generateTodayRuns = async () => {
    setMaterializeMessage('');
    const today = todayIso();
    try {
      const result = await materializeRuns.mutateAsync({
        id: null,
        start_date: today,
        end_date: today,
      });
      setMaterializeMessage(result.created
        ? `${result.created} run(s) created for today.`
        : 'No runs were created. Check that a route is active today, has a default agent, and an active FIELD location is assigned.');
    } catch (requestError) {
      setMaterializeMessage(extractError(requestError, 'Could not generate today\'s runs.'));
    }
  };

  return (
    <div className="w-full space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Field Sales</h1>
        <p className="text-sm text-slate-500">
          Hello {user?.full_name || user?.username}. {formatDate(new Date())}
        </p>
      </div>

      {isLoading && <div className="card animate-pulse h-32" />}

      {activeRuns.map((active) => (
        <div key={active.id} className="card bg-brand-50 border-brand-200">
          <div className="flex justify-between items-start mb-3">
            <div>
              <div className="text-xs uppercase text-brand-700 font-medium">Active Run</div>
              <div className="text-lg font-semibold mt-1">{active.route_name}</div>
              <div className="text-sm text-slate-600">{active.stock_location_name}</div>
            </div>
            <span className="badge-success">In Progress</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm mb-4 sm:grid-cols-4">
            <div>
              <div className="text-slate-500">Cash Collected</div>
              <div className="font-semibold">{formatKes(active.cash_collected)}</div>
            </div>
            <div>
              <div className="text-slate-500">Started</div>
              <div className="font-medium">{active.started_at ? formatDate(active.started_at) : '—'}</div>
            </div>
          </div>
          <div className="flex flex-row gap-2">
            <Link to={`/field/sale/${active.id}`} className="btn-primary flex-1">
              Make a Sale
            </Link>
            <Link to={`/field/complete/${active.id}`} className="btn-secondary flex-1">
              End of Day
            </Link>
          </div>
        </div>
      ))}

      {planned.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Today's Planned Runs</h3>
          <div className="space-y-2">
            {planned.map((run) => (
              <div key={run.id} className="flex flex-col gap-2 border-b border-slate-100 pb-3 last:border-0 sm:flex-row sm:items-center sm:justify-between sm:pb-2">
                <div>
                  <div className="font-medium">{run.route_name}</div>
                  <div className="text-xs text-slate-500">{run.stock_location_name}</div>
                </div>
                <Link to={`/field/start/${run.id}`} className="btn-primary btn-sm">
                  Start
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeRuns.length === 0 && planned.length === 0 && (
        <div className="card text-center py-12">
          <div className="text-4xl mb-3">🚐</div>
          <h3 className="font-semibold mb-1">No runs scheduled today</h3>
          {canManageRuns ? (
            <div className="mt-3 space-y-3">
              <p className="text-sm text-slate-500">
                Review the schedule or generate today&apos;s runs from active routes.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <Button onClick={generateTodayRuns} loading={materializeRuns.isPending}>
                  Generate Today&apos;s Runs
                </Button>
                <Link to="/routes" className="btn-secondary">Routes</Link>
                <Link to="/inventory/locations" className="btn-secondary">Stock Locations</Link>
              </div>
              {materializeMessage && <p className="text-sm text-slate-600" role="status">{materializeMessage}</p>}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Contact the boss to get a run assigned.</p>
          )}
        </div>
      )}
    </div>
  );
}