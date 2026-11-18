import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import DataTable from '@/components/ui/DataTable';
import Input from '@/components/ui/Input';
import PageHeader from '@/components/ui/PageHeader';
import Filter from '@/components/ui/Filter';

export default function RoutesList() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useList('routes', endpoints.routes.list, { search: search || undefined });

  const routes = data?.results || data || [];

  const columns = [
    { key: 'code', label: 'Code', render: (r) => (
      <Link to={`/routes/${r.id}`} className="text-brand-600 font-medium hover:underline">{r.code}</Link>
    )},
    { key: 'name', label: 'Name' },
    { key: 'default_agent_name', label: 'Agent' },
    { key: 'schedule_days', label: 'Schedule', render: (r) => formatDays(r.schedule_days) },
    { key: 'open_runs', label: 'Open Runs', align: 'right' },
    { key: 'is_active', label: 'Active', render: (r) => r.is_active ? '✓' : '✗' },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Routes"
        description="Manage delivery routes, assigned agents, and schedules."
        actions={<Link to="/routes/new" className="btn-primary">+ New Route</Link>}
      />
      <Filter title="Route filters">
        <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </Filter>
      <DataTable columns={columns} rows={routes} loading={isLoading} />
    </div>
  );
}

function formatDays(days) {
  if (!days || !days.length) return '—';
  const names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return days.map((d) => names[d]).join(', ');
}