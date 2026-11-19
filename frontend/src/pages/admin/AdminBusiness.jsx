import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import DataTable from '@/components/ui/DataTable';
import PageHeader from '@/components/ui/PageHeader';

const BUSINESS_FIELDS = [
  ['Business name', 'business_name'],
  ['KRA PIN', 'kra_pin'],
  ['Address', 'address'],
  ['Phone', 'phone'],
  ['Email', 'email'],
  ['Receipt footer', 'receipt_footer'],
];

export default function AdminBusiness() {
  const config = useQuery({
    queryKey: ['business-config'],
    queryFn: async () => (await api.get(endpoints.common.config)).data,
  });
  const taxRates = useQuery({
    queryKey: ['active-tax-rates'],
    queryFn: async () => (await api.get(endpoints.common.taxRates)).data,
  });

  return (
    <div className="space-y-4">
      <PageHeader title="Business Details" description="Business identity used by receipts and active tax rates." />
      {config.isError && <p role="alert" className="text-sm text-red-700">Could not load business details.</p>}
      <section className="card">
        <h2 className="mb-4 text-sm font-semibold text-slate-900">Receipt identity</h2>
        {config.isLoading ? (
          <p role="status" className="text-sm text-slate-500">Loading business details...</p>
        ) : (
          <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
            {BUSINESS_FIELDS.map(([label, key]) => (
              <div key={key} className="min-w-0 border-b border-slate-100 pb-3 last:border-0 sm:last:border-b">
                <dt className="text-xs font-medium uppercase text-slate-500">{label}</dt>
                <dd className="mt-1 break-words text-sm text-slate-900">{config.data?.[key] || '—'}</dd>
              </div>
            ))}
          </dl>
        )}
      </section>
      {taxRates.isError && <p role="alert" className="text-sm text-red-700">Could not load active tax rates.</p>}
      <DataTable
        title="Active tax rates"
        columns={[
          { key: 'name', label: 'Tax' },
          { key: 'rate', label: 'Rate', align: 'right', render: (row) => `${Number(row.rate).toFixed(2)}%` },
        ]}
        rows={taxRates.data || []}
        loading={taxRates.isLoading}
        empty={taxRates.isError ? 'Could not load active tax rates.' : 'No active tax rates.'}
        caption="Active tax rates"
      />
    </div>
  );
}