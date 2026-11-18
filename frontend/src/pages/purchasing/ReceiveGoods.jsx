import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import { formatKes } from '@/utils/money';
import Button from '@/components/ui/Button';
import Select from '@/components/ui/Select';
import Input from '@/components/ui/Input';

export default function ReceiveGoods() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [location, setLocation] = useState('');
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');

  const { data: po } = useQuery({
    queryKey: ['po', id],
    queryFn: async () => (await api.get(endpoints.purchasing.poDetail(id))).data,
  });
  const { data: locations } = useList('locations', endpoints.inventory.locations);

  // Initialize the item table from the PO's outstanding lines once loaded
  if (po && !items) {
    setItems(
      po.items
        .filter((i) => Number(i.remaining_quantity) > 0)
        .map((i) => ({
          product: i.product,
          name: i.product_name,
          sku: i.product_sku,
          quantity_ordered: i.quantity_ordered,
          remaining: i.remaining_quantity,
          quantity_received: i.remaining_quantity,
          unit_cost: i.unit_cost,
        }))
    );
  }

  const submit = useMutation({
    mutationFn: async () => {
      const payload = {
        supplier: po.supplier,
        location,
        po: po.id,
        items: items
          .filter((i) => Number(i.quantity_received) > 0)
          .map((i) => ({
            product: i.product,
            quantity_received: i.quantity_received,
            unit_cost: i.unit_cost,
          })),
      };
      return (await api.post(endpoints.purchasing.grns, payload)).data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['po', id] });
      qc.invalidateQueries({ queryKey: ['pos'] });
      navigate(`/purchasing/grns/${data.id}`);
    },
    onError: (err) => setError(extractError(err)),
  });

  if (!po || !items) return <div>Loading...</div>;

  return (
    <div className="space-y-4 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Receive Goods — {po.po_number}</h1>
        <p className="text-sm text-slate-500">{po.supplier_name}</p>
      </div>

      <div className="card">
        <Select label="Receive Into Location" value={location} onChange={(e) => setLocation(e.target.value)}>
          <option value="">Select location...</option>
          {(locations?.results || locations || []).map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </Select>
      </div>

      <div className="card p-0">
        <table className="table">
          <thead><tr><th>Product</th><th className="text-right">Ordered</th><th className="text-right">Remaining</th><th>Receive Qty</th><th>Unit Cost</th></tr></thead>
          <tbody>
            {items.map((it, idx) => (
              <tr key={it.product}>
                <td>
                  <div className="font-medium">{it.name}</div>
                  <div className="text-xs text-slate-500">{it.sku}</div>
                </td>
                <td className="text-right">{it.quantity_ordered}</td>
                <td className="text-right">{it.remaining}</td>
                <td>
                  <input
                    type="number" min="0" max={it.remaining}
                    className="input w-24"
                    value={it.quantity_received}
                    onChange={(e) => {
                      const copy = [...items];
                      copy[idx].quantity_received = e.target.value;
                      setItems(copy);
                    }}
                  />
                </td>
                <td>
                  <input
                    type="number" step="0.01"
                    className="input w-28"
                    value={it.unit_cost}
                    onChange={(e) => {
                      const copy = [...items];
                      copy[idx].unit_cost = e.target.value;
                      setItems(copy);
                    }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={() => navigate(-1)}>Cancel</Button>
        <Button onClick={() => submit.mutate()} loading={submit.isPending}>
          Post GRN
        </Button>
      </div>
    </div>
  );
}