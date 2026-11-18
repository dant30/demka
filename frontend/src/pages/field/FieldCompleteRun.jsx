import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function FieldCompleteRun() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [cashHandedIn, setCashHandedIn] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');

  const { data: run } = useQuery({
    queryKey: ['run', runId],
    queryFn: async () => (await api.get(endpoints.routes.runDetail(runId))).data,
  });

  const complete = useMutation({
    mutationFn: async () =>
      (await api.post(endpoints.routes.runComplete(runId), {
        cash_handed_in: cashHandedIn,
        notes,
      })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['field-runs'] });
      navigate('/field');
    },
    onError: (err) => setError(extractError(err)),
  });

  if (!run) return <div>Loading...</div>;

  return (
    <div className="w-full min-w-0 space-y-4">
      <h1 className="text-2xl font-bold">Complete Run</h1>

      <div className="card">
        <div className="space-y-3 mb-4">
          <Row label="Route" value={run.route_name} />
          <Row label="Cash Collected" value={formatKes(run.cash_collected)} />
          <Row label="Opening Stock" value={formatKes(run.opening_stock_value)} />
        </div>

        <Input
          label="Cash Handed In (KES)"
          type="number"
          step="0.01"
          value={cashHandedIn}
          onChange={(e) => setCashHandedIn(e.target.value)}
          placeholder="0.00"
        />
        <div className="mt-3">
          <label className="label">Notes (optional)</label>
          <textarea
            className="input"
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any issues, stock discrepancies, etc."
          />
        </div>

        {error && <div className="mt-3 text-sm text-red-600">{error}</div>}

        <Button
          onClick={() => complete.mutate()}
          loading={complete.isPending}
          className="w-full mt-4"
          size="lg"
        >
          Complete Run
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