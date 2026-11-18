import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import DataTable from '@/components/ui/DataTable';
import PageHeader from '@/components/ui/PageHeader';
import Pagination from '@/components/ui/Pagination';

export default function AdminUsers() {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['admin-users', page, search],
    queryFn: async () => (await api.get(endpoints.users.list, {
      params: { page, search: search || undefined, page_size: 25 },
    })).data,
  });

  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const columns = [
    { key: 'username', label: 'Username' },
    { key: 'full_name', label: 'Name' },
    { key: 'phone', label: 'Phone' },
    { key: 'role', label: 'Role' },
    { key: 'is_active', label: 'Active', render: (r) => r.is_active ? '✓' : '✗' },
    { key: 'last_login', label: 'Last Login', render: (r) => r.last_login ? new Date(r.last_login).toLocaleDateString() : 'Never' },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Users"
        description="Manage staff accounts, roles, and sign-in activity."
        actions={<Button onClick={() => setCreateOpen(true)}>+ New User</Button>}
      />

      <div className="card">
        <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <DataTable columns={columns} rows={rows} loading={isLoading} />

      <Pagination page={page} totalPages={totalPages} onChange={setPage} />

      <CreateUserModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSuccess={() => { setCreateOpen(false); refetch(); qc.invalidateQueries({ queryKey: ['admin-users'] }); }}
      />
    </div>
  );
}

function CreateUserModal({ open, onClose, onSuccess }) {
  const [form, setForm] = useState({
    username: '', phone: '', email: '', first_name: '', last_name: '',
    role: 'SALES_HELPER', password: '', confirm_password: '', is_active: true,
  });
  const [error, setError] = useState('');
  const create = useMutation({
    mutationFn: async () => (await api.post(endpoints.users.list, form)).data,
    onSuccess,
    onError: (e) => setError(extractError(e)),
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  return (
    <Modal open={open} onClose={onClose} title="New User" size="lg">
      <div className="grid grid-cols-2 gap-3">
        <Input label="Username" value={form.username} onChange={(e) => set('username', e.target.value)} />
        <Input label="Phone" value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="07XXXXXXXX" />
        <Input label="Email" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
        <Select label="Role" value={form.role} onChange={(e) => set('role', e.target.value)}>
          <option value="SALES_HELPER">Sales Helper</option>
          <option value="FIELD_AGENT">Field Agent</option>
          <option value="BOSS">Boss</option>
          <option value="ADMIN">Admin</option>
        </Select>
        <Input label="First Name" value={form.first_name} onChange={(e) => set('first_name', e.target.value)} />
        <Input label="Last Name" value={form.last_name} onChange={(e) => set('last_name', e.target.value)} />
        <Input label="Password" type="password" value={form.password} onChange={(e) => set('password', e.target.value)} />
        <Input label="Confirm Password" type="password" value={form.confirm_password} onChange={(e) => set('confirm_password', e.target.value)} />
      </div>
      {error && <div className="mt-3 text-sm text-red-600">{error}</div>}
      <Button onClick={() => create.mutate()} loading={create.isPending} className="w-full mt-4">
        Create User
      </Button>
    </Modal>
  );
}