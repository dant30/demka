import { useState } from 'react';
import { useList, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { api } from '@/api/client';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import DataTable from '@/components/ui/DataTable';
import PageHeader from '@/components/ui/PageHeader';
import Switch from '@/components/ui/Switch';
import Pagination from '@/components/ui/Pagination';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Filter from '@/components/ui/Filter';

export default function MpesaReconcile() {
  const [page, setPage] = useState(1);
  const [showUnreconciled, setShowUnreconciled] = useState(true);
  const { data, isLoading, refetch } = useList(
    'mpesa-txns', endpoints.payments.mpesaTransactions,
    { page, reconciled: showUnreconciled ? 'false' : undefined }
  );
  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const [matchTxn, setMatchTxn] = useState(null);

  const columns = [
    { key: 'mpesa_receipt', label: 'M-Pesa Receipt' },
    { key: 'phone', label: 'Phone' },
    { key: 'amount', label: 'Amount', align: 'right', render: (r) => formatKes(r.amount) },
    { key: 'transaction_date', label: 'Date', render: (r) => formatDateTime(r.transaction_date) },
    { key: 'reconciled', label: 'Status', render: (r) => (
      r.reconciled
        ? <span className="badge-success">Matched</span>
        : <span className="badge-warning">Unmatched</span>
    )},
    { key: 'matched_payment_number', label: 'Payment', render: (r) => r.matched_payment_number || '—' },
    { key: 'actions', label: '', render: (r) => !r.reconciled && (
      <button className="text-brand-600 text-sm hover:underline" onClick={() => setMatchTxn(r)}>
        Match Payment
      </button>
    )},
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="M-Pesa Reconciliation"
        description="Match incoming M-Pesa transactions to recorded payments."
      />
      <Filter
        title="Transaction filters"
        activeCount={showUnreconciled ? 1 : 0}
        onClear={() => { setShowUnreconciled(false); setPage(1); }}
        showClear
      >
        <Switch label="Unmatched only" checked={showUnreconciled}
          onChange={(e) => setShowUnreconciled(e.target.checked)} />
      </Filter>
      <DataTable columns={columns} rows={rows} loading={isLoading}
        empty="No M-Pesa transactions to reconcile." />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />

      {matchTxn && (
        <MatchModal
          txn={matchTxn}
          onClose={() => setMatchTxn(null)}
          onSuccess={() => { setMatchTxn(null); refetch(); }}
        />
      )}
    </div>
  );
}

function MatchModal({ txn, onClose, onSuccess }) {
  const [search, setSearch] = useState(txn.phone || '');
  const { data: payments } = useList(
    'pending-payments', endpoints.payments.list,
    { status: 'PENDING', search: search || undefined },
    { enabled: !!search }
  );
  const [selected, setSelected] = useState(null);
  const match = useAction('mpesa', endpoints.payments.mpesaReconcile, { onSuccess });

  const candidates = payments?.results || [];

  return (
    <Modal open onClose={onClose} title="Match M-Pesa Transaction" size="lg">
      <div className="space-y-3">
        <div className="rounded-lg bg-slate-50 p-3">
          <div className="text-sm text-slate-500">Transaction</div>
          <div className="font-medium">{txn.mpesa_receipt} · {formatKes(txn.amount)} · {txn.phone}</div>
        </div>
        <Input
          placeholder="Search pending payments by customer phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="max-h-64 overflow-y-auto space-y-1">
          {candidates.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelected(p)}
              className={`w-full text-left rounded-lg border p-2 ${
                selected?.id === p.id ? 'border-brand-500 bg-brand-50' : 'border-slate-200'
              }`}
            >
              <div className="flex justify-between">
                <span className="font-medium">{p.customer_name}</span>
                <span>{formatKes(p.amount)}</span>
              </div>
              <div className="text-xs text-slate-500">{p.payment_number}</div>
            </button>
          ))}
          {search && candidates.length === 0 && (
            <div className="text-center py-4 text-slate-500 text-sm">No pending payments match.</div>
          )}
        </div>
        <Button
          disabled={!selected}
          loading={match.isPending}
          onClick={() => match.mutate({ id: txn.id, payment: selected.id })}
          className="w-full"
        >
          Match to Payment
        </Button>
      </div>
    </Modal>
  );
}