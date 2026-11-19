import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { useList } from '@/api/queries';
import Button from '@/components/ui/Button';
import ConfirmDialong from '@/components/ui/ConfirmDialong';
import DataTable from '@/components/ui/DataTable';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import Pagination from '@/components/ui/Pagination';
import Select from '@/components/ui/Select';
import Switch from '@/components/ui/Switch';

const PAGE_SIZE = 25;

export default function AdminLocations() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState(null);
  const [removing, setRemoving] = useState(null);
  const [form, setForm] = useState({ user: '', location: '', is_primary: false });
  const [formError, setFormError] = useState('');

  const { data, isLoading, isError } = useList('location-assignments', endpoints.userLocations.list, {
    page, page_size: PAGE_SIZE,
  });
  const { data: userData } = useList('location-assignment-users', endpoints.users.list, {
    is_active: true, page_size: 200,
  });
  const { data: locationData } = useList('location-assignment-locations', endpoints.inventory.locations, {
    page_size: 200,
  });
  const users = userData?.results || userData || [];
  const locations = locationData?.results || locationData || [];
  const rows = data?.results || data || [];

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        user: Number(form.user),
        location: Number(form.location),
        is_primary: form.is_primary,
      };
      return editing
        ? (await api.patch(endpoints.userLocations.detail(editing.id), payload)).data
        : (await api.post(endpoints.userLocations.list, payload)).data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['location-assignments'] });
      setEditing(null);
      setForm({ user: '', location: '', is_primary: false });
      setFormError('');
    },
    onError: (error) => setFormError(extractError(error)),
  });
  const remove = useMutation({
    mutationFn: async () => api.delete(endpoints.userLocations.detail(removing.id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['location-assignments'] });
      setRemoving(null);
    },
  });

  const openForm = (assignment = null) => {
    setEditing(assignment || {});
    setForm({
      user: assignment ? String(assignment.user) : '',
      location: assignment ? String(assignment.location) : '',
      is_primary: assignment?.is_primary || false,
    });
    setFormError('');
    save.reset();
  };

  const columns = [
    { key: 'user_display', label: 'Staff member' },
    { key: 'location_display', label: 'Location' },
    { key: 'is_primary', label: 'Primary', render: (row) => row.is_primary ? 'Yes' : 'No' },
    {
      key: 'actions', label: 'Actions', mobileFullWidth: true,
      render: (row) => (
        <div className="flex w-full flex-col gap-2 sm:flex-row">
          <Button size="sm" variant="secondary" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => openForm(row)}>Edit</Button>
          <Button size="sm" variant="danger" className="min-h-11 w-full sm:min-h-8 sm:w-auto" onClick={() => setRemoving(row)}>Remove</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Staff Locations"
        description="Assign staff to stock locations and choose their primary location."
        actions={<Button className="w-full sm:w-auto" onClick={() => openForm()}>Assign location</Button>}
      />
      {isError && <p className="text-sm text-red-700" role="alert">Could not load location assignments.</p>}
      <DataTable
        columns={columns}
        rows={rows}
        loading={isLoading}
        empty={isError ? 'Could not load assignments.' : 'No staff locations assigned.'}
        caption="Staff location assignments"
      />
      <Pagination page={page} totalPages={data ? Math.ceil(data.count / PAGE_SIZE) : 0} onChange={setPage} />

      <Modal
        open={Boolean(editing)}
        onClose={() => !save.isPending && setEditing(null)}
        title={editing?.id ? 'Edit assignment' : 'Assign staff location'}
        size="sm"
        footer={(
          <div className="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" className="w-full sm:w-auto" onClick={() => setEditing(null)} disabled={save.isPending}>Cancel</Button>
            <Button className="w-full sm:w-auto" onClick={() => save.mutate()} loading={save.isPending} disabled={!form.user || !form.location}>
              Save assignment
            </Button>
          </div>
        )}
      >
        <div className="space-y-4">
          <Select label="Staff member" value={form.user} onChange={(event) => setForm({ ...form, user: event.target.value })}>
            <option value="">Select staff member</option>
            {users.map((user) => <option key={user.id} value={user.id}>{user.full_name || user.username}</option>)}
          </Select>
          <Select label="Stock location" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })}>
            <option value="">Select location</option>
            {locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
          </Select>
          <Switch
            label="Primary location"
            description="Only one primary location is allowed per staff member."
            checked={form.is_primary}
            onChange={(event) => setForm({ ...form, is_primary: event.target.checked })}
          />
          {formError && <p role="alert" className="text-sm text-red-700">{formError}</p>}
        </div>
      </Modal>

      <ConfirmDialong
        open={Boolean(removing)}
        onClose={() => setRemoving(null)}
        onConfirm={() => remove.mutateAsync()}
        loading={remove.isPending}
        error={remove.error ? extractError(remove.error) : ''}
        title="Remove location assignment?"
        description={`Remove ${removing?.location_display || 'this location'} from ${removing?.user_display || 'this staff member'}?`}
        confirmLabel="Remove assignment"
      />
    </div>
  );
}