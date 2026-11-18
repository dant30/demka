import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDetail, useList, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { useAuth } from '@/hooks/useAuth';
import { formatKes, formatNumber } from '@/utils/money';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isBoss } = useAuth();
  const { data: product, isLoading, refetch } = useDetail(
    'product', endpoints.inventory.productDetail(id), id
  );
  const { data: summary } = useDetail(
    'product-summary', endpoints.inventory.productSummary(id), id
  );
  const { data: movements } = useList(
    'product-movements', endpoints.inventory.movements, { product: id, page_size: 20 }
  );

  const [showAdjust, setShowAdjust] = useState(false);
  const [adjustLoc, setAdjustLoc] = useState(null);

  if (isLoading) return <div>Loading...</div>;
  if (!product) return <div>Product not found.</div>;

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex min-w-0 items-center gap-4">
          {product.image ? (
            <img src={product.image} alt={product.name} className="h-20 w-20 shrink-0 rounded-md border border-slate-200 object-cover" />
          ) : (
            <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-md border border-dashed border-slate-300 text-xs text-slate-400">
              No image
            </div>
          )}
          <div className="min-w-0">
            <h1 className="text-2xl font-bold">{product.name}</h1>
            <p className="text-sm text-slate-500">
              SKU: {product.sku}{product.part_number && ` · Part No: ${product.part_number}`}{product.brand && ` · ${product.brand}`}
            </p>
          </div>
        </div>
        {isBoss && (
          <Button variant="secondary" onClick={() => navigate(`/inventory/products/${id}/edit`)}>
            Edit
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card label="Cost" value={product.cost_price ? formatKes(product.cost_price) : 'Hidden'} />
        <Card label="Retail" value={formatKes(product.retail_price)} />
        <Card label="Wholesale" value={formatKes(product.wholesale_price)} />
        <Card label="Reorder Level" value={product.reorder_level} />
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Stock by Location</h3>
          {isBoss && <Button size="sm" onClick={() => setShowAdjust(true)}>Adjust Stock</Button>}
        </div>
        <div className="max-w-full overflow-x-auto">
          <table className="table min-w-[36rem]">
            <thead>
              <tr><th>Location</th><th className="text-right">Quantity</th><th className="text-right">Reorder At</th><th></th></tr>
            </thead>
            <tbody>
              {(summary?.by_location || product.stock_by_location || []).map((l) => (
                <tr key={l.location_id}>
                  <td>{l.location_name}</td>
                  <td className="text-right font-medium">{formatNumber(l.quantity, 0)}</td>
                  <td className="text-right text-slate-500">{l.reorder_level}</td>
                  <td className="text-right">
                    {isBoss && (
                      <button
                        className="text-brand-600 text-sm hover:underline"
                        onClick={() => { setAdjustLoc(l.location_id); setShowAdjust(true); }}
                      >
                        Adjust
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {movements && (movements.results || movements).length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Recent Movements</h3>
          <table className="table">
            <thead><tr><th>Date</th><th>Type</th><th>Location</th><th className="text-right">Qty</th><th>Reference</th></tr></thead>
            <tbody>
              {(movements.results || movements).map((m) => (
                <tr key={m.id}>
                  <td>{m.created_at?.slice(0, 10)}</td>
                  <td>{m.movement_type_display}</td>
                  <td>{m.location_name}</td>
                  <td className={`text-right ${Number(m.quantity) < 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {formatNumber(m.quantity, 0)}
                  </td>
                  <td className="text-xs text-slate-500">{m.reference_type} {m.reference_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <StockAdjustModal
        open={showAdjust}
        onClose={() => setShowAdjust(false)}
        product={product}
        defaultLocation={adjustLoc}
        onSuccess={refetch}
      />
    </div>
  );
}

function StockAdjustModal({ open, onClose, product, defaultLocation, onSuccess }) {
  const [location, setLocation] = useState(defaultLocation || '');
  const [delta, setDelta] = useState('');
  const [notes, setNotes] = useState('');
  const adjust = useAction('adjust', () => endpoints.inventory.stockAdjust, { invalidate: ['product-summary', 'stock-levels'] });
  const { data: locations } = useList('locations', endpoints.inventory.locations);

  const submit = async () => {
    try {
      await adjust.mutateAsync({ id: null, product: product.id, location, delta, notes });
      onSuccess?.();
      onClose();
    } catch (e) {
      alert(e?.response?.data?.error?.message || 'Failed');
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={`Adjust Stock — ${product.name}`}>
      <div className="space-y-3">
        <Select label="Location" value={location} onChange={(e) => setLocation(e.target.value)}>
          <option value="">Select location...</option>
          {(locations?.results || locations || []).map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </Select>
        <Input
          label="Adjustment (positive to add, negative to remove)"
          type="number"
          value={delta}
          onChange={(e) => setDelta(e.target.value)}
          placeholder="e.g. 5 or -3"
        />
        <Input label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        <Button onClick={submit} loading={adjust.isPending} className="w-full">
          Apply Adjustment
        </Button>
      </div>
    </Modal>
  );
}

const Card = ({ label, value }) => (
  <div className="card">
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className="mt-1 font-semibold text-lg">{value}</div>
  </div>
);