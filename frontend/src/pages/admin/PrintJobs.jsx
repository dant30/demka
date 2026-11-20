import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import Button from '@/components/ui/Button';
import ConfirmDialong from '@/components/ui/ConfirmDialong';
import DataTable from '@/components/ui/DataTable';
import Filter from '@/components/ui/Filter';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import Pagination from '@/components/ui/Pagination';
import Select from '@/components/ui/Select';
import { formatDateTime } from '@/utils/dates';

const PAGE_SIZE = 25;
const DOCUMENT_TYPES = [
  ['RECEIPT', 'Sale receipt'],
  ['CREDIT_NOTE', 'Credit note'],
  ['PREORDER_SLIP', 'Preorder slip'],
  ['ROUTE_SHEET', 'Route sheet'],
];

export default function PrintJobs() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [queueType, setQueueType] = useState('RECEIPT');
  const [referenceId, setReferenceId] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);

  const { data, isLoading, isError } = useList('print-jobs', endpoints.printing.jobs, {
    page, page_size: PAGE_SIZE, status: status || undefined,
    document_type: documentType || undefined,
  });
  const sales = useList('print-queue-sales', endpoints.sales.list, { page_size: 200 });
  const returns = useList('print-queue-returns', endpoints.sales.returnsList, { page_size: 200 });
  const preorders = useList('print-queue-preorders', endpoints.preorders.staffList, { page_size: 200 });
  const runs = useList('print-queue-runs', endpoints.routes.runs, { page_size: 200 });
  const detail = useQuery({
    queryKey: ['print-job-detail', selectedJob?.id],
    queryFn: async () => (await api.get(endpoints.printing.jobDetail(selectedJob.id))).data,
    enabled: Boolean(selectedJob?.id),
  });

  const queueMutation = useMutation({
    mutationFn: async () => {
      const routes = {
        RECEIPT: [endpoints.printing.queueReceipt, 'sale'],
        CREDIT_NOTE: [endpoints.printing.queueCreditNote, 'sales_return'],
        PREORDER_SLIP: [endpoints.printing.queuePreorderSlip, 'preorder'],
        ROUTE_SHEET: [endpoints.printing.queueRouteSheet, 'run'],
      };
      const [url, key] = routes[queueType];
      return (await api.post(url, { [key]: Number(referenceId) })).data;
    },
    onSuccess: () => {
      setReferenceId('');
      queryClient.invalidateQueries({ queryKey: ['print-jobs'] });
    },
  });
  const actionMutation = useMutation({
    mutationFn: async ({ job, action }) => {
      const url = action === 'dispatch'
        ? endpoints.printing.jobDispatch(job.id)
        : action === 'retry'
          ? endpoints.printing.jobRetry(job.id)
          : endpoints.printing.jobCancel(job.id);
      return (await api.post(url)).data;
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['print-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['print-job-detail', updated.id] });
      setPendingAction(null);
    },
  });
  const confirmJobAction = (job, action) => {
    actionMutation.reset();
    setPendingAction({ job, action });
  };

  const resourceData = {
    RECEIPT: sales.data,
    CREDIT_NOTE: returns.data,
    PREORDER_SLIP: preorders.data,
    ROUTE_SHEET: runs.data,
  }[queueType];
  const resourceRows = resourceData?.results || resourceData || [];
  const sourceLabel = (row) => row.sale_number
    || row.return_number
    || row.preorder_number
    || `${row.route_code || row.route_name || 'Run'} ${row.run_date || `#${row.id}`}`;

  const columns = [
    { key: 'id', label: 'Job', render: (row) => `#${row.id}` },
    { key: 'document_type_display', label: 'Document' },
    { key: 'reference', label: 'Reference', render: (row) => [row.reference_type, row.reference_id].filter(Boolean).join(' #') || '—' },
    { key: 'printer_name', label: 'Printer' },
    { key: 'status_display', label: 'Status' },
    { key: 'attempts', label: 'Attempts', align: 'right' },
    { key: 'created_at', label: 'Created', render: (row) => formatDateTime(row.created_at) },
    {
      key: 'actions', label: 'Actions', mobileFullWidth: true,
      render: (job) => (
        <div className="flex w-full flex-col gap-2 sm:flex-row sm:flex-wrap">
          <Button size="sm" variant="secondary" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => setSelectedJob(job)}>Details</Button>
          {['QUEUED', 'FAILED'].includes(job.status) && (
            <Button size="sm" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => confirmJobAction(job, 'dispatch')}>Print now</Button>
          )}
          {['FAILED', 'CANCELLED'].includes(job.status) && (
            <Button size="sm" variant="secondary" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => confirmJobAction(job, 'retry')}>Retry</Button>
          )}
          {job.status !== 'PRINTED' && job.status !== 'CANCELLED' && (
            <Button size="sm" variant="danger" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => confirmJobAction(job, 'cancel')}>Cancel</Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Print Jobs" description="Queue documents, inspect printer jobs, and retry failed output." />

      <Filter title="Queue a document" collapsible={false} contentClassName="grid grid-cols-1 items-end gap-3 sm:grid-cols-2 xl:grid-cols-[minmax(12rem,1fr)_minmax(14rem,2fr)_auto]">
        <Select label="Document" value={queueType} onChange={(event) => { setQueueType(event.target.value); setReferenceId(''); queueMutation.reset(); }}>
          {DOCUMENT_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </Select>
        <Select label="Source record" value={referenceId} onChange={(event) => setReferenceId(event.target.value)}>
          <option value="">Select a record</option>
          {resourceRows.map((row) => <option key={row.id} value={row.id}>{sourceLabel(row)}</option>)}
        </Select>
        <Button
          className="min-h-11 w-full sm:w-auto"
          onClick={() => queueMutation.mutate()}
          loading={queueMutation.isPending}
          disabled={!referenceId}
        >
          Queue document
        </Button>
      </Filter>
      {queueMutation.isError && <p role="alert" className="text-sm text-red-700">{extractError(queueMutation.error, 'Could not queue document.')}</p>}
      {queueMutation.isSuccess && <p role="status" className="text-sm text-emerald-700">Document queued successfully.</p>}

      <Filter
        title="Job filters"
        activeCount={[status, documentType].filter(Boolean).length}
        onClear={() => { setStatus(''); setDocumentType(''); setPage(1); }}
        showClear
        contentClassName="grid grid-cols-1 gap-3 sm:grid-cols-2"
      >
        <Select value={status} aria-label="Filter by status" onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="QUEUED">Queued</option>
          <option value="PRINTING">Printing</option>
          <option value="PRINTED">Printed</option>
          <option value="FAILED">Failed</option>
          <option value="CANCELLED">Cancelled</option>
        </Select>
        <Select value={documentType} aria-label="Filter by document" onChange={(event) => { setDocumentType(event.target.value); setPage(1); }}>
          <option value="">All documents</option>
          {[...DOCUMENT_TYPES, ['INVOICE', 'Invoice'], ['DELIVERY_NOTE', 'Delivery note'], ['EXPENSE_SLIP', 'Expense slip'], ['TEST', 'Test print']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </Select>
      </Filter>

      {isError && <p role="alert" className="text-sm text-red-700">Could not load print jobs.</p>}
      <DataTable
        title="Printer queue"
        columns={columns}
        rows={data?.results || []}
        loading={isLoading}
        empty={isError ? 'Could not load print jobs.' : 'No print jobs match these filters.'}
        caption="Print jobs"
      />
      <Pagination page={page} totalPages={data ? Math.ceil(data.count / PAGE_SIZE) : 0} onChange={setPage} />

      <Modal open={Boolean(selectedJob)} onClose={() => setSelectedJob(null)} title={`Print job ${selectedJob ? `#${selectedJob.id}` : ''}`} size="lg">
        {detail.isLoading ? (
          <p role="status" className="text-sm text-slate-500">Loading job details...</p>
        ) : detail.isError ? (
          <p role="alert" className="text-sm text-red-700">Could not load this print job.</p>
        ) : detail.data && (
          <div className="space-y-4">
            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <JobField label="Document" value={detail.data.document_type_display} />
              <JobField label="Status" value={detail.data.status_display} />
              <JobField label="Printer" value={detail.data.printer_name || 'Default printer'} />
              <JobField label="Attempts" value={detail.data.attempts} />
              <JobField label="Created by" value={detail.data.created_by_name || 'System'} />
              <JobField label="Last printed" value={formatDateTime(detail.data.printed_at)} />
            </dl>
            {detail.data.error_message && (
              <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                {detail.data.error_message}
              </div>
            )}
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-900">Document data</h3>
              <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words rounded bg-slate-50 p-3 text-xs text-slate-700">
                {JSON.stringify(detail.data.payload || {}, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Modal>

      <ConfirmDialong
        open={Boolean(pendingAction)}
        onClose={() => !actionMutation.isPending && setPendingAction(null)}
        onConfirm={() => actionMutation.mutateAsync(pendingAction)}
        loading={actionMutation.isPending}
        error={actionMutation.error ? extractError(actionMutation.error) : ''}
        title={pendingAction?.action === 'dispatch' ? 'Print this document now?' : pendingAction?.action === 'retry' ? 'Retry this print job?' : 'Cancel this print job?'}
        description={pendingAction?.action === 'dispatch'
          ? `Send job #${pendingAction.job.id} to ${pendingAction.job.printer_name || 'the default printer'} now.`
          : pendingAction?.action === 'retry'
            ? `Return job #${pendingAction?.job.id} to the queue for another attempt.`
            : `Stop job #${pendingAction?.job.id} from printing. Printed jobs cannot be cancelled.`}
        confirmLabel={pendingAction?.action === 'dispatch' ? 'Print now' : pendingAction?.action === 'retry' ? 'Retry job' : 'Cancel job'}
        variant={pendingAction?.action === 'cancel' ? 'danger' : 'primary'}
      />
    </div>
  );
}

function JobField({ label, value }) {
  return (
    <div className="min-w-0 border-b border-slate-100 pb-2">
      <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm text-slate-900">{value || '—'}</dd>
    </div>
  );
}