import { useEffect, useState } from 'react';
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
import ConfirmDialong from '@/components/ui/ConfirmDialong';

export default function AdminUsers() {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);
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

  const accountAction = useMutation({
    mutationFn: async ({ user, action }) => {
      try {
        if (action === 'delete') {
          await api.delete(endpoints.users.detail(user.id));
        } else {
          await api.patch(endpoints.users.detail(user.id), {
            is_active: action === 'activate',
          });
        }
      } catch (error) {
        throw new Error(extractError(error));
      }
    },
    onSuccess: () => {
      setPendingAction(null);
      qc.invalidateQueries({ queryKey: ['admin-users'] });
    },
  });

  const confirmAccountAction = (user, action) => {
    accountAction.reset();
    setPendingAction({ user, action });
  };

  const columns = [
    { key: 'username', label: 'Username' },
    { key: 'full_name', label: 'Name' },
    { key: 'phone', label: 'Phone' },
    { key: 'role', label: 'Role' },
    { key: 'is_active', label: 'Active', render: (r) => r.is_active ? '✓' : '✗' },
    { key: 'last_login', label: 'Last Login', render: (r) => r.last_login ? new Date(r.last_login).toLocaleDateString() : 'Never' },
    {
      key: 'actions',
      label: 'Actions',
      mobileFullWidth: true,
      render: (r) => (
        <div className="flex w-full gap-2">
          <Button
            size="sm"
            variant="secondary"
            className="min-h-11 min-w-0 flex-1 px-2 md:min-h-8 md:flex-none md:px-0"
            aria-label={`Edit ${r.username}`}
            title="Edit user"
            onClick={() => setEditingUser(r)}
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="m14 5 5 5M4 20l4.5-1 10.8-10.8a2.1 2.1 0 0 0-3-3L5.5 16 4 20Z" />
            </svg>
          </Button>
          <Button
            size="sm"
            variant="secondary"
            className="min-h-11 min-w-0 flex-1 px-2 md:min-h-8 md:flex-none md:px-0"
            aria-label={`${r.is_active ? 'Suspend' : 'Reactivate'} ${r.username}`}
            title={r.is_active ? 'Suspend user' : 'Reactivate user'}
            onClick={() => confirmAccountAction(r, r.is_active ? 'suspend' : 'activate')}
          >
            {r.is_active ? (
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 5v14M16 5v14" />
              </svg>
            ) : (
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="m8 5 11 7-11 7V5Z" />
              </svg>
            )}
          </Button>
          <Button
            size="sm"
            variant="danger"
            className="min-h-11 min-w-0 flex-1 px-2 md:min-h-8 md:flex-none md:px-0"
            aria-label={`Delete ${r.username}`}
            title="Delete user"
            onClick={() => confirmAccountAction(r, 'delete')}
          >
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 7h16M10 11v6M14 11v6M5 7l1 13h12l1-13M9 7V4h6v3" />
            </svg>
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Users"
        description="Manage staff accounts, roles, and sign-in activity."
        actions={<Button onClick={() => setCreateOpen(true)}>+ New User</Button>}
      />

      <div className="w-full max-w-xl">
        <Input
          type="search"
          aria-label="Search users by username, name, or phone"
          placeholder="Search users..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
      </div>

      <DataTable columns={columns} rows={rows} loading={isLoading} />

      <Pagination page={page} totalPages={totalPages} onChange={setPage} />

      <UserFormModal
        key={editingUser?.id || 'new-user'}
        open={createOpen || Boolean(editingUser)}
        user={editingUser}
        onClose={() => { setCreateOpen(false); setEditingUser(null); }}
        onSuccess={() => {
          setCreateOpen(false);
          setEditingUser(null);
          refetch();
          qc.invalidateQueries({ queryKey: ['admin-users'] });
        }}
      />

      <ConfirmDialong
        open={Boolean(pendingAction)}
        onClose={() => setPendingAction(null)}
        onConfirm={() => accountAction.mutateAsync(pendingAction)}
        loading={accountAction.isPending}
        error={accountAction.error?.message}
        title={pendingAction?.action === 'delete' ? 'Delete user?' : pendingAction?.action === 'suspend' ? 'Suspend user?' : 'Reactivate user?'}
        description={pendingAction?.action === 'delete'
          ? `Permanently delete ${pendingAction.user.username}? This cannot be undone.`
          : pendingAction?.action === 'suspend'
            ? `Suspend ${pendingAction.user.username}? They will no longer be able to sign in.`
            : `Allow ${pendingAction?.user.username} to sign in again?`}
        confirmLabel={pendingAction?.action === 'delete' ? 'Delete user' : pendingAction?.action === 'suspend' ? 'Suspend user' : 'Reactivate user'}
        variant={pendingAction?.action === 'activate' ? 'primary' : 'danger'}
      />
    </div>
  );
}

function UserFormModal({ open, onClose, onSuccess, user }) {
  const [form, setForm] = useState({
    username: '', phone: '', email: '', first_name: '', last_name: '',
    role: 'SALES_HELPER', password: '', confirm_password: '', is_active: true,
  });
  const [error, setError] = useState('');
  const save = useMutation({
    mutationFn: async () => {
      const payload = user
        ? {
            email: form.email,
            first_name: form.first_name,
            last_name: form.last_name,
            phone: form.phone,
            role: form.role,
          }
        : form;
      return user
        ? (await api.patch(endpoints.users.detail(user.id), payload)).data
        : (await api.post(endpoints.users.list, payload)).data;
    },
    onSuccess,
    onError: (e) => setError(extractError(e)),
  });
  useEffect(() => {
    setForm(user ? {
      username: user.username || '',
      phone: user.phone || '',
      email: user.email || '',
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      role: user.role || 'SALES_HELPER',
      password: '',
      confirm_password: '',
      is_active: user.is_active,
    } : {
      username: '', phone: '', email: '', first_name: '', last_name: '',
      role: 'SALES_HELPER', password: '', confirm_password: '', is_active: true,
    });
    setError('');
  }, [user, open]);

  const set = (k, v) => setForm({ ...form, [k]: v });

  return (
    <Modal open={open} onClose={onClose} title={user ? 'Edit User' : 'New User'} size="lg">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Input label="Username" value={form.username} onChange={(e) => set('username', e.target.value)} readOnly={Boolean(user)} />
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
        {!user && <Input label="Password" type="password" value={form.password} onChange={(e) => set('password', e.target.value)} />}
        {!user && <Input label="Confirm Password" type="password" value={form.confirm_password} onChange={(e) => set('confirm_password', e.target.value)} />}
      </div>
      {error && <div className="mt-3 text-sm text-red-600">{error}</div>}
      <Button onClick={() => save.mutate()} loading={save.isPending} className="mt-4 w-full">
        {user ? 'Save Changes' : 'Create User'}
      </Button>
    </Modal>
  );
}