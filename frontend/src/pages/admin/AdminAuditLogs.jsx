import { useState } from 'react';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatDateTime } from '@/utils/dates';
import DataTable from '@/components/ui/DataTable';
import DatePicker from '@/components/ui/DatePicker';
import Filter from '@/components/ui/Filter';
import Input from '@/components/ui/Input';
import PageHeader from '@/components/ui/PageHeader';
import Pagination from '@/components/ui/Pagination';
import Select from '@/components/ui/Select';

const PAGE_SIZE = 25;

export default function AdminAuditLogs() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [action, setAction] = useState('');
  const [modelName, setModelName] = useState('');
  const [user, setUser] = useState('');
  const [after, setAfter] = useState('');
  const [before, setBefore] = useState('');
  const { data: userData } = useList('audit-log-users', endpoints.users.list, { page_size: 200 });
  const users = userData?.results || userData || [];
  const activeFilterCount = [action, modelName, user, after, before].filter(Boolean).length;
  const clearFilters = () => {
    setSearch('');
    setAction('');
    setModelName('');
    setUser('');
    setAfter('');
    setBefore('');
    setPage(1);
  };
  const params = {
    page,
    page_size: PAGE_SIZE,
    search: search || undefined,
    action: action || undefined,
    model_name: modelName || undefined,
    user: user || undefined,
    created_after: after ? `${after}T00:00:00` : undefined,
    created_before: before ? `${before}T23:59:59` : undefined,
  };
  const { data, isLoading, isError } = useList('audit-logs', endpoints.auditLogs.list, params);
  const rows = data?.results || [];

  const columns = [
    { key: 'created_at', label: 'Time', render: (row) => formatDateTime(row.created_at) },
    { key: 'user_display', label: 'Staff', render: (row) => row.user_display || 'System' },
    { key: 'action', label: 'Action' },
    { key: 'target', label: 'Record', render: (row) => `${row.model_name} #${row.object_id || '—'}` },
    { key: 'ip_address', label: 'IP Address' },
    {
      key: 'changes', label: 'Changes', mobileFullWidth: true,
      render: (row) => (
        <details className="max-w-full">
          <summary className="cursor-pointer text-brand-700">View details</summary>
          <pre className="mt-2 max-h-48 max-w-full overflow-auto whitespace-pre-wrap break-words rounded bg-slate-50 p-2 text-xs">
            {JSON.stringify(row.changes || {}, null, 2)}
          </pre>
        </details>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Audit Log" description="Review recorded staff actions and changes." />
      <Filter
        title="Audit filters"
        headerContent={(
          <Input
            type="search"
            aria-label="Search audit actions, records, or staff"
            placeholder="Search audit logs..."
            value={search}
            onChange={(event) => { setSearch(event.target.value); setPage(1); }}
          />
        )}
        activeCount={activeFilterCount}
        onClear={clearFilters}
        showClear
        contentClassName="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3"
      >
        <Input label="Action" value={action} onChange={(event) => { setAction(event.target.value); setPage(1); }} placeholder="e.g. UPDATE" />
        <Input label="Model" value={modelName} onChange={(event) => { setModelName(event.target.value); setPage(1); }} placeholder="e.g. Sale" />
        <Select label="Staff member" value={user} onChange={(event) => { setUser(event.target.value); setPage(1); }}>
          <option value="">All staff</option>
          {users.map((staff) => <option key={staff.id} value={staff.id}>{staff.full_name || staff.username}</option>)}
        </Select>
        <DatePicker label="From" value={after} onChange={(value) => { setAfter(value); setPage(1); }} />
        <DatePicker label="Through" value={before} onChange={(value) => { setBefore(value); setPage(1); }} />
      </Filter>
      {isError && <p className="text-sm text-red-700" role="alert">Could not load audit history.</p>}
      <DataTable
        title="Recorded activity"
        columns={columns}
        rows={rows}
        loading={isLoading}
        empty={isError ? 'Could not load audit history.' : 'No audit entries match these filters.'}
        caption="Audit history"
      />
      <Pagination page={page} totalPages={data ? Math.ceil(data.count / PAGE_SIZE) : 0} onChange={setPage} />
    </div>
  );
}