import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import DataTable from '@/components/ui/DataTable';
import PageHeader from '@/components/ui/PageHeader';
import Switch from '@/components/ui/Switch';

export default function AdminPrinters() {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const { data, isLoading, refetch } = useList('printers', endpoints.printing.printers);

  const printers = data?.results || data || [];

  const testPrint = async (id) => {
    setTestResult(null);
    try {
      const res = await api.post(endpoints.printing.testPrint(id));
      setTestResult({ ok: res.data.status === 'PRINTED', ...res.data });
    } catch (err) {
      setTestResult({ ok: false, error: extractError(err) });
    }
  };

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'printer_type_display', label: 'Type' },
    { key: 'transport_summary', label: 'Connection' },
    { key: 'paper_width_mm', label: 'Paper', render: (r) => `${r.paper_width_mm}mm` },
    { key: 'assigned_location_name', label: 'Location', render: (r) => r.assigned_location_name || '—' },
    { key: 'is_default', label: 'Default', render: (r) => r.is_default ? '✓' : '' },
    { key: 'actions', label: '', render: (r) => (
      <button className="text-brand-600 text-sm hover:underline" onClick={() => testPrint(r.id)}>
        Test Print
      </button>
    )},
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Printers"
        description="Configure receipt printers and test their connections."
        actions={<Button onClick={() => setCreateOpen(true)}>+ New Printer</Button>}
      />

      {testResult && (
        <div className={`card ${testResult.ok ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          {testResult.ok
            ? `✓ Test print sent successfully (job #${testResult.job_id}).`
            : `✗ Print failed: ${testResult.error || testResult.error_message}`}
        </div>
      )}

      <DataTable columns={columns} rows={printers} loading={isLoading} />

      <CreatePrinterModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSuccess={() => { setCreateOpen(false); refetch(); qc.invalidateQueries({ queryKey: ['printers'] }); }}
      />
    </div>
  );
}

function CreatePrinterModal({ open, onClose, onSuccess }) {
  const { data: locations } = useList('locations', endpoints.inventory.locations);
  const [form, setForm] = useState({
    name: '', printer_type: 'NETWORK', paper_width_mm: 58,
    ip_address: '', port: 9100, identifier: '',
    usb_vendor_id: '', usb_product_id: '',
    bt_mac_address: '', bt_rfcomm_channel: 1,
    assigned_location: '', is_default: false,
  });
  const create = useMutation({
    mutationFn: async () => (await api.post(endpoints.printing.printers, form)).data,
    onSuccess,
  });

  const set = (k, v) => setForm({ ...form, [k]: v });

  return (
    <Modal open={open} onClose={onClose} title="New Printer" size="lg">
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Name" value={form.name} onChange={(e) => set('name', e.target.value)} />
          <Select label="Type" value={form.printer_type} onChange={(e) => set('printer_type', e.target.value)}>
            <option value="NETWORK">Network / WiFi</option>
            <option value="USB">USB</option>
            <option value="BLUETOOTH">Bluetooth (shop PC)</option>
          </Select>
          <Select label="Paper Width" value={form.paper_width_mm} onChange={(e) => set('paper_width_mm', Number(e.target.value))}>
            <option value={58}>58 mm</option>
            <option value={80}>80 mm</option>
          </Select>
          <Select label="Assigned Location" value={form.assigned_location} onChange={(e) => set('assigned_location', e.target.value)}>
            <option value="">None</option>
            {(locations?.results || locations || []).map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </Select>
        </div>

        {form.printer_type === 'NETWORK' && (
          <div className="grid grid-cols-2 gap-3">
            <Input label="IP Address" value={form.ip_address} onChange={(e) => set('ip_address', e.target.value)} />
            <Input label="Port" type="number" value={form.port} onChange={(e) => set('port', Number(e.target.value))} />
          </div>
        )}

        {form.printer_type === 'USB' && (
          <div className="grid grid-cols-2 gap-3">
            <Input label="Vendor ID" value={form.usb_vendor_id} onChange={(e) => set('usb_vendor_id', e.target.value)} placeholder="0x04b8" />
            <Input label="Product ID" value={form.usb_product_id} onChange={(e) => set('usb_product_id', e.target.value)} placeholder="0x0202" />
          </div>
        )}

        {form.printer_type === 'BLUETOOTH' && (
          <div className="grid grid-cols-2 gap-3">
            <Input label="MAC Address" value={form.bt_mac_address} onChange={(e) => set('bt_mac_address', e.target.value)} placeholder="00:11:22:33:44:55" />
            <Input label="RFCOMM Channel" type="number" value={form.bt_rfcomm_channel} onChange={(e) => set('bt_rfcomm_channel', Number(e.target.value))} />
            <Input label="Serial Path (identifier)" value={form.identifier} onChange={(e) => set('identifier', e.target.value)} placeholder="/dev/rfcomm0 or COM4" className="col-span-2" />
          </div>
        )}

        <Switch
          label="Default printer"
          description="Use this printer for new receipts."
          checked={form.is_default}
          onChange={(e) => set('is_default', e.target.checked)}
        />

        <Button onClick={() => create.mutate()} loading={create.isPending} className="w-full">
          Create Printer
        </Button>
      </div>
    </Modal>
  );
}