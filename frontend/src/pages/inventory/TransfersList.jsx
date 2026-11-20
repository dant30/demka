import { useState } from 'react';
import { useList, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatDateTime } from '@/utils/dates';
import DataTable from '@/components/ui/DataTable';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import ConfirmDialong from '@/components/ui/ConfirmDialong';
import Select from '@/components/ui/Select';
import TextareaField from '@/components/ui/TextareaField';
import Input from '@/components/ui/Input';

export default function TransfersList() {
  const [page, setPage] = useState(1);
  const { data, isLoading, refetch } = useList('transfers', endpoints.inventory.transfers, { page });
  const [createOpen, setCreateOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState(null);
  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const dispatch = useAction('transfer', endpoints.inventory.transferDispatch, { invalidate: ['transfers'] });
  const receive = useAction('transfer', endpoints.inventory.transferReceive, { invalidate: ['transfers'] });
  const cancel = useAction('transfer', endpoints.inventory.transferCancel, { invalidate: ['transfers'] });

  const columns = [
    { key: 'id', label: '#', render: (r) => `#${r.id}` },
    { key: 'from_location_name', label: 'From' },
    { key: 'to_location_name', label: 'To' },
    { key: 'status_display', label: 'Status' },
    { key: 'item_count', label: 'Items', align: 'right' },
    { key: 'created_at', label: 'Created', render: (r) => formatDateTime(r.created_at) },
    { key: 'actions', label: 'Actions', render: (r) => (
      <div className="flex gap-2 justify-end">
        {r.status === 'PENDING' && (
          <button className="text-brand-600 text-xs hover:underline" onClick={async (e) => { e.stopPropagation(); await dispatch.mutateAsync({ id: r.id }); refetch(); }}>
            Dispatch
          </button>
        )}
        {r.status === 'IN_TRANSIT' && (
          <>
            <button className="text-green-600 text-xs hover:underline" onClick={async (e) => { e.stopPropagation(); await receive.mutateAsync({ id: r.id }); refetch(); }}>
              Receive
            </button>
            <button type="button" className="text-red-600 text-xs hover:underline" onClick={(e) => { e.stopPropagation(); setCancelTarget(r); }}>
              Cancel
            </button>
          </>
        )}
      </div>
    )},
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setCreateOpen(true)}>+ New Transfer</Button>
      </div>
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <CreateTransferModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSuccess={() => { setCreateOpen(false); refetch(); }}
      />
      <ConfirmDialong
        open={!!cancelTarget}
        onClose={() => setCancelTarget(null)}
        onConfirm={async () => {
          await cancel.mutateAsync({ id: cancelTarget.id });
          refetch();
        }}
        title="Cancel stock transfer?"
        description={cancelTarget ? `Transfer #${cancelTarget.id} will be cancelled.` : ''}
        confirmLabel="Cancel transfer"
        loading={cancel.isPending}
      />
    </div>
  );
}

function CreateTransferModal({ open, onClose, onSuccess }) {
  const { data: locations } = useList('locations', endpoints.inventory.locations);
  const { data: products } = useList('products', endpoints.inventory.products, { page_size: 300 });
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [items, setItems] = useState([]);
  const [notes, setNotes] = useState('');
  const [productToAdd, setProductToAdd] = useState('');
  const [error, setError] = useState('');
  const create = useAction('transfers', () => endpoints.inventory.transfers, {
    invalidate: ['transfers'], onSuccess,
  });

  const submit = async () => {
    if (!from || !to || from === to) {
      setError('Choose two different locations.');
      return;
    }
    if (!items.length) {
      setError('Add at least one item.');
      return;
    }
    setError('');
    await create.mutateAsync({ id: null, from_location: from, to_location: to, items, notes });
  };

  const addItem = (pid) => {
    const p = (products?.results || products || []).find((x) => x.id === Number(pid));
    if (!p) return;
    if (items.find((i) => i.product_id === p.id)) return;
    setItems([...items, { product_id: p.id, name: p.name, sku: p.sku, quantity: 1 }]);
  };

  return (
    <Modal open={open} onClose={onClose} title="New Transfer" size="lg" footer={
      <>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button onClick={submit} loading={create.isPending}>Create Transfer</Button>
      </>
    }>
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Select aria-label="Source location" value={from} onChange={(e) => setFrom(e.target.value)}>
            <option value="">From...</option>
            {(locations?.results || locations || []).map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </Select>
          <Select aria-label="Destination location" value={to} onChange={(e) => setTo(e.target.value)}>
            <option value="">To...</option>
            {(locations?.results || locations || []).map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </Select>
        </div>

        <Select label="Add product" searchable value={productToAdd} onChange={(e) => { addItem(e.target.value); setProductToAdd(''); }}>
          <option value="">Add product...</option>
          {(products?.results || products || []).map((p) => (
            <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
          ))}
        </Select>

        <table className="table">
          <thead><tr><th>Item</th><th>Qty</th><th></th></tr></thead>
          <tbody>
            {items.map((it, idx) => (
              <tr key={it.product_id}>
                <td>{it.name} <span className="text-xs text-slate-500">{it.sku}</span></td>
                <td>
                  <Input
                    type="number" min="1" className="w-20"
                    value={it.quantity}
                    onChange={(e) => {
                      const copy = [...items];
                      copy[idx].quantity = Number(e.target.value);
                      setItems(copy);
                    }}
                  />
                </td>
                <td><button onClick={() => setItems(items.filter((_, i) => i !== idx))} className="text-red-600">✕</button></td>
              </tr>
            ))}
          </tbody>
        </table>

        <TextareaField label="Notes" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        {error && <p className="field-error" role="alert">{error}</p>}
      </div>
    </Modal>
  );
}