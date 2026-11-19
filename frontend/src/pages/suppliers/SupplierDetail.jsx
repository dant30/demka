import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useDetail, useList, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { useAuth } from '@/hooks/useAuth';
import { formatKes } from '@/utils/money';
import Button from '@/components/ui/Button';

const TABS = ['Overview', 'Products', 'Purchase Orders'];

export default function SupplierDetail() {
  const { id } = useParams();
  const { isBoss } = useAuth();
  const [tab, setTab] = useState('Overview');
  const { data: supplier, isLoading } = useDetail('supplier', endpoints.suppliers.detail(id), id);
  const { data: stats } = useDetail('supplier-stats', endpoints.suppliers.stats(id), id);

  if (isLoading) return <div>Loading...</div>;
  if (!supplier) return <div>Not found</div>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">{supplier.name}</h1>
          <p className="text-sm text-slate-500">{supplier.code} · {supplier.phone}</p>
        </div>
        {isBoss && <Link to={`/suppliers/${id}/edit`} className="btn-secondary">Edit</Link>}
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Products" value={stats.product_count} />
          <Stat label="Purchase Orders" value={stats.purchase_order_count} />
          <Stat label="Cheapest Price" value={stats.cheapest_purchase_price ? formatKes(stats.cheapest_purchase_price) : '—'} />
          <Stat label="Avg Lead Time" value={stats.average_lead_time_days ? `${stats.average_lead_time_days}d` : '—'} />
        </div>
      )}

      <div className="border-b border-slate-200">
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium border-b-2 ${
                tab === t ? 'border-brand-600 text-brand-600' : 'border-transparent text-slate-500'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {tab === 'Overview' && (
        <div className="card space-y-2 text-sm">
          <Row label="Email" value={supplier.email || '—'} />
          <Row label="KRA PIN" value={supplier.kra_pin || '—'} />
          <Row label="Address" value={supplier.address || '—'} />
          <Row label="Payment Terms" value={`${supplier.payment_terms_days} days`} />
          <Row label="Active" value={supplier.is_active ? 'Yes' : 'No'} />
        </div>
      )}
      {tab === 'Products' && <ProductsTab supplierId={supplier.id} />}
      {tab === 'Purchase Orders' && <PurchaseOrdersTab supplierId={supplier.id} />}
    </div>
  );
}

function ProductsTab({ supplierId }) {
  const { data } = useList('supplier-products', endpoints.suppliers.products(supplierId));
  const rows = data || [];
  return (
    <div className="card p-0">
      <table className="table">
        <thead><tr><th>Product</th><th>SKU</th><th>Supplier PN</th><th className="text-right">Last Price</th><th className="text-right">Lead Time</th></tr></thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={5} className="text-center py-8 text-slate-500">No products linked.</td></tr>
          ) : rows.map((r) => (
            <tr key={r.id}>
              <td>{r.product_display}</td>
              <td className="text-xs text-slate-500">{r.product_sku}</td>
              <td>{r.supplier_part_number || '—'}</td>
              <td className="text-right">{r.last_purchase_price ? formatKes(r.last_purchase_price) : '—'}</td>
              <td className="text-right">{r.lead_time_days}d</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PurchaseOrdersTab({ supplierId }) {
  const { data } = useList('supplier-pos', endpoints.purchasing.pos, { supplier: supplierId });
  const rows = data?.results || [];
  return (
    <div className="card p-0">
      <table className="table">
        <thead><tr><th>PO #</th><th>Status</th><th className="text-right">Total</th><th>Created</th></tr></thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={4} className="text-center py-8 text-slate-500">No POs yet.</td></tr>
          ) : rows.map((r) => (
            <tr key={r.id}>
              <td>{r.po_number}</td>
              <td>{r.status_display}</td>
              <td className="text-right">{formatKes(r.total)}</td>
              <td>{r.created_at?.slice(0, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const Stat = ({ label, value }) => (
  <div className="card">
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className="mt-1 text-xl font-semibold">{value}</div>
  </div>
);

const Row = ({ label, value }) => (
  <div className="flex justify-between"><span className="text-slate-500">{label}</span><span>{value}</span></div>
);