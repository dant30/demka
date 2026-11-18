import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCreate, useDetail, useList, useUpdate } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { extractError } from '@/api/client';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import TextareaField from '@/components/ui/TextareaField';
import PageHeader from '@/components/ui/PageHeader';
import FormSection from '@/components/forms/FormSection';
import FormActions from '@/components/forms/FormActions';
import CheckBox from '@/components/ui/CheckBox';

const DAYS = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
];

export default function RouteForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [form, setForm] = useState({
    code: '',
    name: '',
    description: '',
    default_agent: '',
    schedule_days: [],
    is_active: true,
  });
  const { data: existingRoute, isLoading: routeLoading } = useDetail(
    'route',
    id ? endpoints.routes.detail(id) : null,
    id,
  );
  const { data: agentData, isLoading: agentsLoading } = useList(
    'route-agents',
    endpoints.users.list,
    { is_active: true, page_size: 200 },
  );
  const agents = (agentData?.results || agentData || []).filter(
    (agent) => ['FIELD_AGENT', 'BOSS', 'ADMIN'].includes(agent.role),
  );
  const create = useCreate('routes', endpoints.routes.list, {
    invalidate: ['routes'],
    onSuccess: (route) => navigate(`/routes/${route.id}`),
  });
  const update = useUpdate('routes', endpoints.routes.detail, {
    invalidate: ['routes'],
    onSuccess: (route) => navigate(`/routes/${route.id}`),
  });

  useEffect(() => {
    if (!existingRoute) return;
    setForm({
      code: existingRoute.code || '',
      name: existingRoute.name || '',
      description: existingRoute.description || '',
      default_agent: existingRoute.default_agent ? String(existingRoute.default_agent) : '',
      schedule_days: existingRoute.schedule_days || [],
      is_active: existingRoute.is_active,
    });
  }, [existingRoute]);

  const setField = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const toggleDay = (day) => {
    setForm((current) => ({
      ...current,
      schedule_days: current.schedule_days.includes(day)
        ? current.schedule_days.filter((value) => value !== day)
        : [...current.schedule_days, day].sort((a, b) => a - b),
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    try {
      const payload = {
        ...form,
        code: form.code.trim().toUpperCase(),
        default_agent: form.default_agent || null,
      };
      if (id) await update.mutateAsync({ id, payload });
      else await create.mutateAsync(payload);
    } catch {
      // The mutation error is rendered below.
    }
  };

  if (id && routeLoading) return <p className="text-slate-500">Loading route...</p>;

  const mutationError = id ? update.error : create.error;
  const isPending = id ? update.isPending : create.isPending;

  return (
    <form onSubmit={submit} className="page-form">
      <PageHeader
        title={id ? 'Edit Route' : 'New Route'}
        description={id ? 'Update route details, its default field agent, and weekly schedule.' : 'Set up a route, its default field agent, and weekly schedule.'}
        backTo={id ? `/routes/${id}` : '/routes'}
        backLabel="Routes"
      />

      <FormSection title="Route details" description="Choose a unique route code and name">
        <Input
          label="Route code"
          value={form.code}
          onChange={(event) => setField('code', event.target.value)}
          maxLength={20}
          required
          autoCapitalize="characters"
        />
        <Input
          label="Route name"
          value={form.name}
          onChange={(event) => setField('name', event.target.value)}
          maxLength={100}
          required
        />
        <Select
          label="Default field agent"
          value={form.default_agent}
          onChange={(value) => setField('default_agent', value)}
          options={[
            { value: '', label: 'No default agent', sublabel: 'Can be assigned later' },
            ...agents.map((agent) => ({
              value: agent.id,
              label: agent.full_name || agent.username,
              sublabel: agent.username,
            })),
          ]}
          searchable
          disabled={agentsLoading}
          hint={agentsLoading ? 'Loading agents...' : 'Optional; can be assigned later.'}
        />
        <CheckBox
          label="Route is active"
          checked={form.is_active}
          onChange={(event) => setField('is_active', event.target.checked)}
          className="sm:col-span-2"
        />
      </FormSection>

      <FormSection title="Weekly schedule" description="Select the days this route is planned to run" columns={1}>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
          {DAYS.map((day) => (
            <div key={day.value} className="rounded-md border border-slate-200 px-3 hover:bg-slate-50">
              <CheckBox
                label={day.label}
                checked={form.schedule_days.includes(day.value)}
                onChange={() => toggleDay(day.value)}
              />
            </div>
          ))}
        </div>
      </FormSection>

      <FormSection title="Description" columns={1}>
        <TextareaField
          label="Notes"
          value={form.description}
          onChange={(event) => setField('description', event.target.value)}
          rows={3}
          maxLength={2000}
          hint="Optional details for route coordinators."
        />
      </FormSection>

      {mutationError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {extractError(mutationError, id ? 'Could not update route.' : 'Could not create route.')}
        </div>
      )}

      <FormActions>
        <Button type="button" variant="secondary" onClick={() => navigate(id ? `/routes/${id}` : '/routes')}>
          Cancel
        </Button>
        <Button type="submit" loading={isPending}>
          {id ? 'Save Changes' : 'Create Route'}
        </Button>
      </FormActions>
    </form>
  );
}
