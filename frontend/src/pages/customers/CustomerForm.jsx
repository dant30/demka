import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAction, useCreate, useDetail, useList, useUpdate } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { useAuth } from '@/hooks/useAuth';
import { extractError } from '@/api/client';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import FormSection from '@/components/forms/FormSection';
import FormActions from '@/components/forms/FormActions';
import TextareaField from '@/components/ui/TextareaField';
import PageHeader from '@/components/ui/PageHeader';

export default function CustomerForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const { isBoss } = useAuth();
  const [error, setError] = useState('');
  const [routeId, setRouteId] = useState('');
  const [form, setForm] = useState({
    name: '', phone: '', email: '', customer_type: 'RETAIL',
    business_name: '', kra_pin: '', physical_address: '',
    credit_limit: 0, payment_terms_days: 0,
  });
  const { data: existing, isLoading } = useDetail(
    'customer', endpoints.customers.detail(id), id,
  );
  const { data: routesData, isLoading: routesLoading } = useList(
    'customer-route-options', endpoints.routes.list,
    { is_active: true, page_size: 100 },
  );
  const routes = routesData?.results || routesData || [];
  const currentRoute = existing?.current_route;

  useEffect(() => {
    if (!existing) return;
    setForm({
      name: existing.name || '',
      phone: existing.phone || '',
      email: existing.email || '',
      customer_type: existing.customer_type || 'RETAIL',
      business_name: existing.business_name || '',
      kra_pin: existing.kra_pin || '',
      physical_address: existing.physical_address || '',
      credit_limit: existing.credit_limit ?? 0,
      payment_terms_days: existing.payment_terms_days ?? 0,
    });
    setRouteId(currentRoute?.route_id ? String(currentRoute.route_id) : '');
  }, [existing, currentRoute]);

  const create = useCreate('customers', endpoints.customers.list, { invalidate: ['customers'] });
  const update = useUpdate('customer', endpoints.customers.detail, {
    invalidate: ['customer'],
  });
  const assignRoute = useAction('assign-customer-route', endpoints.customers.assignRoute, {
    invalidate: ['customer', 'route-assignments'],
  });

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    const payload = { ...form };
    if (isEdit && !isBoss) delete payload.credit_limit;
    let customer;
    try {
      customer = isEdit
        ? await update.mutateAsync({ id, payload })
        : await create.mutateAsync(payload);
    } catch (err) {
      setError(extractError(err, 'Could not save customer.'));
      return;
    }

    const savedCustomerId = isEdit ? id : customer?.id;
    if (!savedCustomerId) {
      setError('Customer saved, but its ID was not returned. Reopen the customer and assign the route from its detail page.');
      return;
    }

    const previousRouteId = existing?.current_route?.route_id;
    if (routeId && Number(routeId) !== previousRouteId) {
      try {
        await assignRoute.mutateAsync({
          id: savedCustomerId,
          route: Number(routeId),
          reason: 'Assigned from customer form',
        });
      } catch (err) {
        navigate(`/customers/${savedCustomerId}`, {
          state: { routeAssignmentError: extractError(err, 'Route assignment failed.') },
        });
        return;
      }
    }
    navigate(`/customers/${savedCustomerId}`);
  };

  const set = (k, v) => {
    setForm({ ...form, [k]: v });
    if (k === 'customer_type' && v === 'WALK_IN') setRouteId('');
  };

  if (isEdit && isLoading) return <div>Loading customer...</div>;

  return (
    <form onSubmit={submit} className="page-form">
      <PageHeader
        title={isEdit ? 'Edit Customer' : 'New Customer'}
        description={isEdit ? 'Update customer details and account terms.' : 'Add a customer and configure their account terms.'}
      />
      <FormSection title="Customer details" description="Contact information and account terms">
        <Input label="Name" value={form.name} onChange={(e) => set('name', e.target.value)} required />
        <Input label="Phone" value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="07XXXXXXXX" required />
        <Input label="Email" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
        <Select label="Type" value={form.customer_type} onChange={(e) => set('customer_type', e.target.value)}>
          <option value="RETAIL">Retail</option>
          <option value="RESELLER">Reseller</option>
          <option value="WALK_IN">Walk-in</option>
        </Select>
        <Input label="Business Name" value={form.business_name} onChange={(e) => set('business_name', e.target.value)} />
        <Input label="KRA PIN" value={form.kra_pin} onChange={(e) => set('kra_pin', e.target.value)} />
        {(!isEdit || isBoss) && <Input label="Credit Limit" type="number" value={form.credit_limit} onChange={(e) => set('credit_limit', e.target.value)} />}
        <Input label="Payment Terms (days)" type="number" value={form.payment_terms_days} onChange={(e) => set('payment_terms_days', e.target.value)} />
        {form.customer_type !== 'WALK_IN' && (
          <Select
            label="Delivery Route (optional)"
            value={routeId}
            onChange={setRouteId}
            disabled={routesLoading}
            hint={routesLoading ? 'Loading routes...' : 'Choose the active route that serves this customer.'}
            options={[
              { value: '', label: isEdit ? 'No route change' : 'No route assignment' },
              ...(currentRoute && !routes.some((route) => route.id === currentRoute.route_id)
                ? [{ value: currentRoute.route_id, label: `${currentRoute.route_code} — ${currentRoute.route_name}` }]
                : []),
              ...routes.map((route) => ({
                value: route.id,
                label: `${route.code} — ${route.name}`,
              })),
            ]}
          />
        )}
      </FormSection>
      <FormSection title="Address" columns={1}>
        <TextareaField label="Physical Address" rows={3} value={form.physical_address} onChange={(e) => set('physical_address', e.target.value)} />
      </FormSection>
      {error && <div role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      <FormActions>
        <Button variant="secondary" type="button" onClick={() => navigate(-1)}>Cancel</Button>
        <Button type="submit" loading={create.isPending || update.isPending || assignRoute.isPending}>
          {isEdit ? 'Save Changes' : 'Create Customer'}
        </Button>
      </FormActions>
    </form>
  );
}