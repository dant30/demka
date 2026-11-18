import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import { formatDateTime } from '@/utils/dates';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import DataTable from '@/components/ui/DataTable';
import PageHeader from '@/components/ui/PageHeader';
import MetricCard from '@/components/cards/MetricCard';
import ConfirmDialong from '@/components/ui/ConfirmDialong';

export default function AdminEtims() {
  const qc = useQueryClient();
  const [error, setError] = useState('');
  const [confirmInit, setConfirmInit] = useState(false);

  const { data: config } = useQuery({
    queryKey: ['etims-config'],
    queryFn: async () => (await api.get(endpoints.etims.config)).data,
  });
  const { data: invoices } = useList('etims-invoices', endpoints.etims.invoices, { page_size: 10 });
  const { data: health } = useQuery({
    queryKey: ['etims-health-admin'],
    queryFn: async () => (await api.get(endpoints.reporting.etimsHealth)).data,
  });

  const [form, setForm] = useState({
    environment: 'sandbox', tin: '', bhf_id: '00',
    device_serial: '', cmc_key: '',
  });

  const updateConfig = useMutation({
    mutationFn: async () => (await api.patch(endpoints.etims.config, form)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['etims-config'] }),
    onError: (e) => setError(extractError(e)),
  });

  const initDevice = useMutation({
    mutationFn: async () => (await api.post(endpoints.etims.config)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['etims-config'] }),
    onError: (e) => setError(extractError(e)),
  });

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader title="eTIMS Configuration" description="Manage device registration and monitor submission health." />

      {health && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Submitted" value={health.submitted} accent="brand" />
          <MetricCard label="Failed" value={health.failed + health.rejected} accent="danger" />
          <MetricCard label="Success Rate" value={`${health.success_rate_pct}%`} accent="success" />
          <MetricCard label="Total" value={health.total} accent="warning" />
        </div>
      )}

      <div className="card">
        <h3 className="font-semibold mb-3">Device Configuration</h3>
        {config && (
          <div className="space-y-1 text-sm mb-4">
            <Row label="Status" value={config.cmc_key_set ? '✅ Initialised' : '❌ Not initialised'} />
            <Row label="Environment" value={config.environment} />
            <Row label="TIN" value={config.tin || '—'} />
            <Row label="Branch" value={config.bhf_id} />
            <Row label="Serial" value={config.device_serial} />
            <Row label="Last Sync" value={config.last_code_sync_at ? formatDateTime(config.last_code_sync_at) : '—'} />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Select label="Environment" value={form.environment} onChange={(e) => setForm({ ...form, environment: e.target.value })}>
            <option value="sandbox">Sandbox</option>
            <option value="production">Production</option>
          </Select>
          <Input label="TIN" value={form.tin} onChange={(e) => setForm({ ...form, tin: e.target.value })} />
          <Input label="Branch ID" value={form.bhf_id} onChange={(e) => setForm({ ...form, bhf_id: e.target.value })} />
          <Input label="Device Serial" value={form.device_serial} onChange={(e) => setForm({ ...form, device_serial: e.target.value })} />
        </div>

        {error && <div className="mt-3 text-sm text-red-600">{error}</div>}

        <div className="mt-4 flex gap-2">
          <Button onClick={() => updateConfig.mutate()} loading={updateConfig.isPending}>
            Save Configuration
          </Button>
          <Button variant="secondary" onClick={() => setConfirmInit(true)} loading={initDevice.isPending}>
            Initialise Device
          </Button>
        </div>
      </div>

      {invoices && (
        <DataTable
          title="Recent Submissions"
          caption="Recent eTIMS submissions"
          columns={[
            { key: 'invoice_number', label: 'Invoice' },
            { key: 'receipt_type_display', label: 'Type' },
            { key: 'status_display', label: 'Status' },
            { key: 'submitted_at', label: 'Submitted', render: (row) => row.submitted_at ? formatDateTime(row.submitted_at) : '—' },
          ]}
          rows={invoices.results || invoices}
        />
      )}

      <ConfirmDialong
        open={confirmInit}
        onClose={() => setConfirmInit(false)}
        onConfirm={() => initDevice.mutateAsync()}
        title="Initialise eTIMS device?"
        description="This registers the device with KRA and replaces its current CMC key."
        confirmLabel="Initialise device"
        loading={initDevice.isPending}
      />
    </div>
  );
}

const Row = ({ label, value }) => (
  <div className="flex justify-between"><span className="text-slate-500">{label}</span><span>{value}</span></div>
);