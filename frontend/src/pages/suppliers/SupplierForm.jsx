import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useCreate, useUpdate } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import Input from '@/components/ui/Input';
import Switch from '@/components/ui/Switch';
import Button from '@/components/ui/Button';
import FormSection from '@/components/forms/FormSection';
import FormActions from '@/components/forms/FormActions';
import TextareaField from '@/components/ui/TextareaField';
import PageHeader from '@/components/ui/PageHeader';

export default function SupplierForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const { data: existing } = useQuery({
    queryKey: ['supplier-edit', id],
    queryFn: async () => (await api.get(endpoints.suppliers.detail(id))).data,
    enabled: isEdit,
  });
  const [form, setForm] = useState({
    code: '', name: '', phone: '', email: '',
    kra_pin: '', address: '', payment_terms_days: 0, is_active: true,
  });
  useEffect(() => {
    if (existing) setForm((current) => ({ ...current, ...existing }));
  }, [existing]);
  const create = useCreate('suppliers', endpoints.suppliers.list, {
    onSuccess: (d) => navigate(`/suppliers/${d.id}`),
  });
  const update = useUpdate('suppliers', endpoints.suppliers.detail, {
    onSuccess: () => navigate(`/suppliers/${id}`),
  });
  const set = (k, v) => setForm({ ...form, [k]: v });
  const submit = async (event) => {
    event.preventDefault();
    if (isEdit) {
      const payload = {
        name: form.name,
        phone: form.phone,
        email: form.email,
        kra_pin: form.kra_pin,
        address: form.address,
        payment_terms_days: form.payment_terms_days,
        is_active: form.is_active,
      };
      await update.mutateAsync({ id, payload });
    } else {
      await create.mutateAsync(form);
    }
  };

  return (
    <form onSubmit={submit} className="page-form">
      <PageHeader
        title={`${isEdit ? 'Edit' : 'New'} Supplier`}
        description="Manage supplier contact details and payment terms."
      />
      <FormSection title="Supplier details" description="Primary contact and payment terms">
        <Input label="Code (optional)" value={form.code} onChange={(e) => set('code', e.target.value)} hint="Leave blank to auto-generate" />
        <Input label="Name" value={form.name} onChange={(e) => set('name', e.target.value)} required />
        <Input label="Phone" value={form.phone} onChange={(e) => set('phone', e.target.value)} />
        <Input label="Email" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
        <Input label="KRA PIN" value={form.kra_pin} onChange={(e) => set('kra_pin', e.target.value)} />
        <Input label="Payment Terms (days)" type="number" value={form.payment_terms_days} onChange={(e) => set('payment_terms_days', e.target.value)} />
        <Switch label="Active" checked={form.is_active} onChange={(e) => set('is_active', e.target.checked)} />
      </FormSection>
      <FormSection title="Address" columns={1}>
        <TextareaField label="Address" rows={3} value={form.address} onChange={(e) => set('address', e.target.value)} />
      </FormSection>
      <FormActions>
        <Button variant="secondary" type="button" onClick={() => navigate(-1)}>Cancel</Button>
        <Button type="submit" loading={create.isPending || update.isPending}>
          {isEdit ? 'Save Changes' : 'Create'}
        </Button>
      </FormActions>
    </form>
  );
}