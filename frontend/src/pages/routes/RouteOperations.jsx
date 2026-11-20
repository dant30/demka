import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import Button from '@/components/ui/Button';
import ConfirmDialong from '@/components/ui/ConfirmDialong';
import DataTable from '@/components/ui/DataTable';
import DatePicker from '@/components/ui/DatePicker';
import Filter from '@/components/ui/Filter';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import Pagination from '@/components/ui/Pagination';
import Select from '@/components/ui/Select';
import Switch from '@/components/ui/Switch';
import Tabs from '@/components/ui/Tabs';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';

const PAGE_SIZE = 25;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const CHANGE_TYPES = [
  ['REASSIGN_CUSTOMER', 'Reassign customer'],
  ['REASSIGN_AGENT', 'Reassign agent'],
  ['ROUTE_MERGE', 'Route merge'],
  ['ROUTE_SPLIT', 'Route split'],
  ['DEACTIVATE', 'Deactivate'],
];

export default function RouteOperations() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState('schedules');
  const [scheduleEditor, setScheduleEditor] = useState(null);
  const [scheduleDelete, setScheduleDelete] = useState(null);
  const [scheduleForm, setScheduleForm] = useState({ route: '', day_of_week: '', is_active: true });
  const [scheduleError, setScheduleError] = useState('');
  const [logPage, setLogPage] = useState(1);
  const [routeFilter, setRouteFilter] = useState('');
  const [changeType, setChangeType] = useState('');
  const [changedAfter, setChangedAfter] = useState('');
  const [changedBefore, setChangedBefore] = useState('');
  const [daysBack, setDaysBack] = useState('7');

  const routesQuery = useList('routes', endpoints.routes.list, { page_size: 200 });
  const schedulesQuery = useList('route-schedules', endpoints.routes.schedules);
  const routes = routesQuery.data?.results || routesQuery.data || [];
  const routeNames = Object.fromEntries(routes.map((route) => [route.id, `${route.code} · ${route.name}`]));
  const schedules = (schedulesQuery.data?.results || schedulesQuery.data || []).map((schedule) => ({
    ...schedule,
    route_display: routeNames[schedule.route] || `Route #${schedule.route}`,
  }));

  const logParams = {
    page: logPage,
    page_size: PAGE_SIZE,
    route: routeFilter || undefined,
    change_type: changeType || undefined,
    changed_after: changedAfter ? `${changedAfter}T00:00:00` : undefined,
    changed_before: changedBefore ? `${changedBefore}T23:59:59` : undefined,
  };
  const logsQuery = useList('route-change-log', endpoints.routes.changeLog, logParams);
  const varianceQuery = useList('route-variance', endpoints.routes.runVarianceReport, { days_back: daysBack });
  const historyFilterCount = [routeFilter, changeType, changedAfter, changedBefore].filter(Boolean).length;
  const clearHistoryFilters = () => {
    setRouteFilter('');
    setChangeType('');
    setChangedAfter('');
    setChangedBefore('');
    setLogPage(1);
  };

  const saveSchedule = useMutation({
    mutationFn: async () => {
      const payload = {
        route: Number(scheduleForm.route),
        day_of_week: Number(scheduleForm.day_of_week),
        is_active: scheduleForm.is_active,
      };
      return scheduleEditor?.id
        ? (await api.patch(endpoints.routes.scheduleDetail(scheduleEditor.id), payload)).data
        : (await api.post(endpoints.routes.schedules, payload)).data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['route-schedules'] });
      setScheduleEditor(null);
      setScheduleError('');
    },
    onError: (error) => setScheduleError(extractError(error)),
  });
  const deleteSchedule = useMutation({
    mutationFn: async () => api.delete(endpoints.routes.scheduleDetail(scheduleDelete.id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['route-schedules'] });
      setScheduleDelete(null);
    },
  });

  const openScheduleEditor = (schedule = null) => {
    setScheduleEditor(schedule || {});
    setScheduleForm({
      route: schedule ? String(schedule.route) : '',
      day_of_week: schedule ? String(schedule.day_of_week) : '',
      is_active: schedule?.is_active ?? true,
    });
    setScheduleError('');
    saveSchedule.reset();
  };

  const scheduleColumns = [
    { key: 'route_display', label: 'Route' },
    { key: 'day_name', label: 'Day' },
    { key: 'is_active', label: 'Active', render: (row) => row.is_active ? 'Yes' : 'No' },
    {
      key: 'actions', label: 'Actions', mobileFullWidth: true,
      render: (row) => (
        <div className="flex w-full flex-col gap-2 sm:flex-row">
          <Button size="sm" variant="secondary" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => openScheduleEditor(row)}>Edit</Button>
          <Button size="sm" variant="danger" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => setScheduleDelete(row)}>Delete</Button>
        </div>
      ),
    },
  ];
  const logColumns = [
    { key: 'changed_at', label: 'Changed', render: (row) => formatDateTime(row.changed_at) },
    { key: 'route_code', label: 'Route' },
    { key: 'change_type_display', label: 'Change' },
    { key: 'agents', label: 'Agent', render: (row) => [row.previous_agent_name, row.new_agent_name].filter(Boolean).join(' → ') || '—' },
    { key: 'affected_customers', label: 'Customers', align: 'right', render: (row) => Array.isArray(row.affected_customers) ? row.affected_customers.length : '—' },
    { key: 'reason', label: 'Reason', mobileFullWidth: true },
    { key: 'changed_by_name', label: 'Changed by' },
  ];
  const varianceColumns = [
    { key: 'run_date', label: 'Run date' },
    { key: 'route', label: 'Route', render: (row) => `${row.route.code} · ${row.route.name}` },
    { key: 'agent', label: 'Agent', render: (row) => row.agent.name },
    { key: 'cash_expected', label: 'Expected', align: 'right' },
    { key: 'cash_handed_in', label: 'Handed in', align: 'right' },
    { key: 'variance', label: 'Variance', align: 'right', render: (row) => (
      <span className={Number(row.variance) === 0 ? '' : 'font-semibold text-red-700'}>{formatKes(row.variance)}</span>
    )},
  ];

  const tabs = [
    {
      value: 'schedules', label: 'Schedules', content: (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button className="min-h-11 w-full sm:w-auto" onClick={() => openScheduleEditor()}>Add schedule</Button>
          </div>
          {schedulesQuery.isError && <p role="alert" className="text-sm text-red-700">Could not load schedules.</p>}
          <DataTable
            columns={scheduleColumns}
            rows={schedules}
            loading={schedulesQuery.isLoading || routesQuery.isLoading}
            empty={schedulesQuery.isError ? 'Could not load schedules.' : 'No route schedules configured.'}
            caption="Route schedules"
          />
        </div>
      ),
    },
    {
      value: 'history', label: 'Change history', content: (
        <div className="space-y-4">
          <Filter title="History filters" activeCount={historyFilterCount} onClear={clearHistoryFilters} showClear contentClassName="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Select label="Route" value={routeFilter} onChange={(event) => { setRouteFilter(event.target.value); setLogPage(1); }}>
              <option value="">All routes</option>
              {routes.map((route) => <option key={route.id} value={route.id}>{route.code} · {route.name}</option>)}
            </Select>
            <Select label="Change type" value={changeType} onChange={(event) => { setChangeType(event.target.value); setLogPage(1); }}>
              <option value="">All changes</option>
              {CHANGE_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </Select>
            <DatePicker label="From" value={changedAfter} onChange={(value) => { setChangedAfter(value); setLogPage(1); }} />
            <DatePicker label="Through" value={changedBefore} onChange={(value) => { setChangedBefore(value); setLogPage(1); }} />
          </Filter>
          {logsQuery.isError && <p role="alert" className="text-sm text-red-700">Could not load route history.</p>}
          <DataTable
            title="Route changes"
            columns={logColumns}
            rows={logsQuery.data?.results || []}
            loading={logsQuery.isLoading}
            empty={logsQuery.isError ? 'Could not load route history.' : 'No route changes match these filters.'}
            caption="Route change history"
          />
          <Pagination page={logPage} totalPages={logsQuery.data ? Math.ceil(logsQuery.data.count / PAGE_SIZE) : 0} onChange={setLogPage} />
        </div>
      ),
    },
    {
      value: 'variance', label: 'Cash variance', content: (
        <div className="space-y-4">
          <Filter
            title="Variance period"
            activeCount={daysBack !== '7' ? 1 : 0}
            onClear={() => setDaysBack('7')}
            showClear
          >
            <Select label="Look back" value={daysBack} onChange={(event) => setDaysBack(event.target.value)} className="w-full sm:max-w-xs">
              <option value="7">Last 7 days</option>
              <option value="14">Last 14 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </Select>
          </Filter>
          {varianceQuery.isError && <p role="alert" className="text-sm text-red-700">Could not load cash variance.</p>}
          <DataTable
            title="Completed runs with cash variance"
            columns={varianceColumns}
            rows={varianceQuery.data || []}
            loading={varianceQuery.isLoading}
            empty={varianceQuery.isError ? 'Could not load cash variance.' : 'No cash variance in this period.'}
            caption="Route cash variance"
          />
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Route Operations" description="Schedules, route changes, and completed-run cash variance." />
      <Tabs tabs={tabs} value={tab} onChange={setTab} tabListClassName="-mx-1" />

      <Modal
        open={Boolean(scheduleEditor)}
        onClose={() => !saveSchedule.isPending && setScheduleEditor(null)}
        title={scheduleEditor?.id ? 'Edit route schedule' : 'Add route schedule'}
        size="sm"
        footer={(
          <div className="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" className="w-full sm:w-auto" onClick={() => setScheduleEditor(null)} disabled={saveSchedule.isPending}>Cancel</Button>
            <Button className="w-full sm:w-auto" onClick={() => saveSchedule.mutate()} loading={saveSchedule.isPending} disabled={!scheduleForm.route || scheduleForm.day_of_week === ''}>Save schedule</Button>
          </div>
        )}
      >
        <div className="space-y-4">
          <Select label="Route" value={scheduleForm.route} onChange={(event) => setScheduleForm({ ...scheduleForm, route: event.target.value })}>
            <option value="">Select route</option>
            {routes.map((route) => <option key={route.id} value={route.id}>{route.code} · {route.name}</option>)}
          </Select>
          <Select label="Day of week" value={scheduleForm.day_of_week} onChange={(event) => setScheduleForm({ ...scheduleForm, day_of_week: event.target.value })}>
            <option value="">Select day</option>
            {DAYS.map((day, index) => <option key={day} value={index}>{day}</option>)}
          </Select>
          <Switch label="Schedule active" checked={scheduleForm.is_active} onChange={(event) => setScheduleForm({ ...scheduleForm, is_active: event.target.checked })} />
          {scheduleError && <p role="alert" className="text-sm text-red-700">{scheduleError}</p>}
        </div>
      </Modal>
      <ConfirmDialong
        open={Boolean(scheduleDelete)}
        onClose={() => setScheduleDelete(null)}
        onConfirm={() => deleteSchedule.mutateAsync()}
        loading={deleteSchedule.isPending}
        error={deleteSchedule.error ? extractError(deleteSchedule.error) : ''}
        title="Delete route schedule?"
        description={`Remove the ${scheduleDelete?.day_name || ''} schedule for ${routeNames[scheduleDelete?.route] || 'this route'}?`}
        confirmLabel="Delete schedule"
      />
    </div>
  );
}