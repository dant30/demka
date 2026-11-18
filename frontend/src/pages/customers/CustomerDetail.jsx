import { useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useAction, useDetail, useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { extractError } from '@/api/client';
import { formatKes } from '@/utils/money';
import { formatDate, formatDateTime } from '@/utils/dates';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Select from '@/components/ui/Select';
import Input from '@/components/ui/Input';

const TABS = ['Overview', 'Sales', 'Credit Ledger', 'Route History'];

export default function CustomerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [tab, setTab] = useState('Overview');
  const [showAssignRoute, setShowAssignRoute] = useState(false);
  const { data: customer, isLoading } = useDetail(
    'customer', endpoints.customers.detail(id), id
  );

  if (isLoading) return <div>Loading...</div>;
  if (!customer) return <div>Not found</div>;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{customer.name}</h1>
          <p className="text-sm text-slate-500">
            {customer.code} · {customer.phone} · {customer.customer_type_display}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate(`/customers/${id}/edit`)}>Edit</Button>
          <Button variant="secondary" onClick={() => setShowAssignRoute(true)}>Assign Route</Button>
        </div>
      </div>

      {location.state?.routeAssignmentError && (
        <div role="alert" className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Customer saved, but route assignment failed: {location.state.routeAssignmentError}
        </div>
      )}

      <div className="card">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Credit Limit" value={formatKes(customer.credit_limit)} />
          <Stat
            label="Outstanding Balance"
            value={formatKes(customer.current_balance)}
            danger={Number(customer.current_balance) > 0}
          />
          <Stat label="Available Credit" value={formatKes(Number(customer.credit_limit) - Number(customer.current_balance))} />
          <Stat label="Payment Terms" value={`${customer.payment_terms_days} days`} />
        </div>
      </div>

      <div className="border-b border-slate-200">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                tab === t
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div>
        {tab === 'Overview' && (
          <OverviewTab customer={customer} onAssignRoute={() => setShowAssignRoute(true)} />
        )}
        {tab === 'Sales' && <SalesTab customerId={customer.id} />}
        {tab === 'Credit Ledger' && <CreditLedgerTab customerId={customer.id} />}
        {tab === 'Route History' && <RouteHistoryTab customerId={customer.id} />}
      </div>
      <AssignRouteModal
        open={showAssignRoute}
        onClose={() => setShowAssignRoute(false)}
        customerId={customer.id}
      />
    </div>
  );
}

function OverviewTab({ customer, onAssignRoute }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="card">
        <h3 className="font-semibold mb-3">Contact</h3>
        <div className="space-y-2 text-sm">
          <Row label="Phone" value={customer.phone} />
          <Row label="Email" value={customer.email || '—'} />
          <Row label="Address" value={customer.physical_address || '—'} />
          <Row label="KRA PIN" value={customer.kra_pin || '—'} />
          <Row label="Business" value={customer.business_name || '—'} />
        </div>
      </div>
      <div className="card">
        <h3 className="font-semibold mb-3">Current Route</h3>
        {customer.current_route ? (
          <div className="space-y-2 text-sm">
            <Row label="Route" value={`${customer.current_route.route_code} — ${customer.current_route.route_name}`} />
            <Row label="Since" value={formatDate(customer.current_route.assigned_from)} />
          </div>
        ) : (
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-slate-500">Not assigned to a route.</p>
            <Button size="sm" variant="secondary" onClick={onAssignRoute}>
              Assign
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function AssignRouteModal({ open, onClose, customerId }) {
  const [routeId, setRouteId] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const { data, isLoading } = useList(
    'routes', endpoints.routes.list, { is_active: true, page_size: 100 }, { enabled: open },
  );
  const routes = data?.results || data || [];
  const assignRoute = useAction('assign-customer-route', endpoints.customers.assignRoute, {
    invalidate: ['customer', 'route-assignments'],
    onSuccess: () => {
      setRouteId('');
      setReason('');
      onClose();
    },
  });

  const submit = async () => {
    if (!routeId) {
      setError('Choose a route first.');
      return;
    }
    setError('');
    try {
      await assignRoute.mutateAsync({
        id: customerId,
        route: Number(routeId),
        reason,
      });
    } catch (err) {
      setError(extractError(err, 'Could not assign route.'));
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Assign Customer to Route"
      footer={(
        <>
          <Button variant="secondary" type="button" onClick={onClose}>Cancel</Button>
          <Button type="button" onClick={submit} loading={assignRoute.isPending} disabled={!routes.length}>
            Assign Route
          </Button>
        </>
      )}
    >
      <div className="space-y-4">
        <Select
          label="Active Route"
          value={routeId}
          onChange={setRouteId}
          required
          disabled={isLoading || !routes.length}
          options={[
            { value: '', label: isLoading ? 'Loading routes...' : 'Select a route...' },
            ...routes.map((route) => ({
              value: route.id,
              label: `${route.code} — ${route.name}`,
            })),
          ]}
        />
        {!isLoading && !routes.length && (
          <p className="text-sm text-slate-500">There are no active routes to assign.</p>
        )}
        <Input label="Reason (optional)" value={reason} onChange={(event) => setReason(event.target.value)} />
        {error && <div role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      </div>
    </Modal>
  );
}

function SalesTab({ customerId }) {
  const { data } = useList('customer-sales', endpoints.sales.list, { customer: customerId });
  const sales = data?.results || [];
  return (
    <div className="card p-0">
      <table className="table">
        <thead><tr><th>Sale #</th><th>Date</th><th>Status</th><th className="text-right">Total</th><th className="text-right">Balance</th></tr></thead>
        <tbody>
          {sales.length === 0 ? (
            <tr><td colSpan={5} className="text-center py-8 text-slate-500">No sales yet.</td></tr>
          ) : sales.map((s) => (
            <tr key={s.id}>
              <td>{s.sale_number}</td>
              <td>{formatDate(s.created_at)}</td>
              <td>{s.status_display}</td>
              <td className="text-right">{formatKes(s.total)}</td>
              <td className={`text-right ${Number(s.balance_due) > 0 ? 'text-red-600' : ''}`}>
                {formatKes(s.balance_due)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CreditLedgerTab({ customerId }) {
  const { data } = useList('customer-ledger', endpoints.payments.ledger, { customer: customerId });
  const rows = data?.results || data || [];
  return (
    <div className="card p-0">
      <table className="table">
        <thead><tr><th>Date</th><th>Type</th><th>Reference</th><th className="text-right">Amount</th><th className="text-right">Balance</th></tr></thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={5} className="text-center py-8 text-slate-500">No ledger entries.</td></tr>
          ) : rows.map((r) => (
            <tr key={r.id}>
              <td>{formatDateTime(r.created_at)}</td>
              <td>{r.entry_type_display}</td>
              <td className="text-xs text-slate-500">{r.reference_type} {r.reference_id}</td>
              <td className={`text-right ${Number(r.amount) < 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatKes(r.amount)}
              </td>
              <td className="text-right font-medium">{formatKes(r.balance_after)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RouteHistoryTab({ customerId }) {
  const { data: assignments } = useList(
    'route-assignments',
    endpoints.customers.routeAssignments,
    { customer: customerId },
  );
  const rows = assignments?.results || assignments || [];
  return (
    <div className="card p-0">
      <table className="table">
        <thead><tr><th>Route</th><th>From</th><th>To</th><th>Reason</th></tr></thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={4} className="text-center py-8 text-slate-500">No route history.</td></tr>
          ) : rows.map((a) => (
            <tr key={a.id}>
              <td>{a.route_display}</td>
              <td>{formatDate(a.assigned_from)}</td>
              <td>{a.assigned_to ? formatDate(a.assigned_to) : <span className="badge-success">Current</span>}</td>
              <td className="text-sm text-slate-600">{a.reason || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const Stat = ({ label, value, danger }) => (
  <div>
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className={`text-xl font-semibold mt-1 ${danger ? 'text-red-600' : 'text-slate-900'}`}>{value}</div>
  </div>
);

const Row = ({ label, value }) => (
  <div className="flex justify-between"><span className="text-slate-500">{label}</span><span>{value}</span></div>
);