import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import Button from '@/components/ui/Button';

export default function FieldStartRun() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [error, setError] = useState('');

  const { data: run, isLoading } = useQuery({
    queryKey: ['run', runId],
    queryFn: async () => (await api.get(endpoints.routes.runDetail(runId))).data,
  });

  const start = useMutation({
    mutationFn: async () => (await api.post(endpoints.routes.runStart(runId))).data,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['field-runs'] });
      qc.invalidateQueries({ queryKey: ['run', runId] });
      navigate('/field');
    },
    onError: (err) => setError(extractError(err)),
  });

  if (isLoading) return <div>Loading...</div>;
  if (!run) return <div>Run not found.</div>;

  return (
    <div className="w-full max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">Start Run</h1>
      <div className="card">
        <div className="space-y-3">
          <Row label="Route" value={run.route_name} />
          <Row label="Van" value={run.stock_location_name} />
          <Row label="Date" value={run.run_date} />
        </div>
        <div className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
          Starting locks in the opening stock value for reconciliation at end of day.
        </div>
        {error && <div className="mt-3 text-sm text-red-600">{error}</div>}
        <Button
          onClick={() => start.mutate()}
          loading={start.isPending}
          className="w-full mt-4"
          size="lg"
        >
          Start Run
        </Button>
      </div>
    </div>
  );
}

const Row = ({ label, value }) => (
  <div className="flex justify-between text-sm">
    <span className="text-slate-500">{label}</span>
    <span className="font-medium">{value || '—'}</span>
  </div>
);