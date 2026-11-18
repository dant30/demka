import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreate, useList } from '@/api/queries';
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
  const [form, setForm] = useState({
    code: '',
    name: '',
    description: '',
    default_agent: '',
    schedule_days: [],
    is_active: true,
  });
  const { data: agentData, isLoading: agentsLoading } = useList(
    'route-agents',
    endpoints.users.list,
    { role: 'FIELD_AGENT', is_active: true, page_size: 200 },
  );
  const agents = agentData?.results || agentData || [];
  const create = useCreate('routes', endpoints.routes.list, {
    invalidate: ['routes'],
    onSuccess: (route) => navigate(`/routes/${route.id}`),
  });

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
      await create.mutateAsync({
        ...form,
        code: form.code.trim().toUpperCase(),
        default_agent: form.default_agent || null,
      });
    } catch {
      // The mutation error is rendered below.
    }
  };

  return (
    <form onSubmit={submit} className="page-form">
      <PageHeader
        title="New Route"
        description="Set up a route, its default field agent, and weekly schedule."
        backTo="/routes"
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

      {create.error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {extractError(create.error, 'Could not create route.')}
        </div>
      )}

      <FormActions>
        <Button type="button" variant="secondary" onClick={() => navigate('/routes')}>
          Cancel
        </Button>
        <Button type="submit" loading={create.isPending}>
          Create Route
        </Button>
      </FormActions>
    </form>
  );
}
