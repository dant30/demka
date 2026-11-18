import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function SupplierReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());

  const { data } = useQuery({
    queryKey: ['supplier-purchases', params],
    queryFn: async () => (await api.get(endpoints.reporting.purchasesBySupplier, { params })).data,
  });

  return (
    <div className="space-y-4">
      <ReportHeader title="Supplier Report" description="Purchase spend by supplier" />
      {data && (
        <DataTable
          columns={[
            { key: 'name', label: 'Supplier', render: (row) => <span>{row.name} <span className="text-xs text-slate-500">{row.code}</span></span> },
            { key: 'po_count', label: 'PO Count', align: 'right' },
            { key: 'total_spent', label: 'Total Spend', align: 'right', render: (row) => formatKes(row.total_spent) },
          ]}
          rows={data}
          keyField="supplier_id"
          caption="Supplier purchases report"
        />
      )}
    </div>
  );
}