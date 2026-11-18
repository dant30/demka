import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreate } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import FormSection from '@/components/forms/FormSection';
import FormActions from '@/components/forms/FormActions';
import TextareaField from '@/components/ui/TextareaField';
import PageHeader from '@/components/ui/PageHeader';

export default function SupplierForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    code: '', name: '', phone: '', email: '',
    kra_pin: '', address: '', payment_terms_days: 0,
  });
  const create = useCreate('suppliers', endpoints.suppliers.list, {
    onSuccess: (d) => navigate(`/suppliers/${d.id}`),
  });
  const set = (k, v) => setForm({ ...form, [k]: v });

  return (
    <form onSubmit={(e) => { e.preventDefault(); create.mutateAsync(form); }} className="page-form">
      <PageHeader title="New Supplier" description="Add supplier contact details and payment terms." />
      <FormSection title="Supplier details" description="Primary contact and payment terms">
        <Input label="Code (optional)" value={form.code} onChange={(e) => set('code', e.target.value)} hint="Leave blank to auto-generate" />
        <Input label="Name" value={form.name} onChange={(e) => set('name', e.target.value)} required />
        <Input label="Phone" value={form.phone} onChange={(e) => set('phone', e.target.value)} />
        <Input label="Email" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
        <Input label="KRA PIN" value={form.kra_pin} onChange={(e) => set('kra_pin', e.target.value)} />
        <Input label="Payment Terms (days)" type="number" value={form.payment_terms_days} onChange={(e) => set('payment_terms_days', e.target.value)} />
      </FormSection>
      <FormSection title="Address" columns={1}>
        <TextareaField label="Address" rows={3} value={form.address} onChange={(e) => set('address', e.target.value)} />
      </FormSection>
      <FormActions>
        <Button variant="secondary" type="button" onClick={() => navigate(-1)}>Cancel</Button>
        <Button type="submit" loading={create.isPending}>Create</Button>
      </FormActions>
    </form>
  );
}