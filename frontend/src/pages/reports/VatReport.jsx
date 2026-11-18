import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { ReportHeader } from './ReportLayout';
import DataTable from '@/components/ui/DataTable';

export default function VatReport() {
  const [searchParams] = useSearchParams();
  const params = Object.fromEntries(searchParams.entries());

  const { data } = useQuery({
    queryKey: ['vat', params],
    queryFn: async () => (await api.get(endpoints.reporting.vat, { params })).data,
  });

  return (
    <div className="space-y-4">
      <ReportHeader title="VAT Summary" description="KRA-ready output for your accountant" />

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div className="card">
              <div className="text-xs text-slate-500 uppercase">Total Taxable Base</div>
              <div className="text-2xl font-bold mt-1">{formatKes(data.total_taxable_base)}</div>
            </div>
            <div className="card">
              <div className="text-xs text-slate-500 uppercase">Total VAT</div>
              <div className="text-2xl font-bold mt-1">{formatKes(data.total_vat)}</div>
            </div>
          </div>

          <DataTable
            columns={[
              { key: 'code', label: 'Code', render: (row) => <span className="font-mono">{row.code}</span> },
              { key: 'name', label: 'Type' },
              { key: 'rate', label: 'Rate', align: 'right', render: (row) => `${row.rate}%` },
              { key: 'gross_sales', label: 'Gross Sales', align: 'right', render: (row) => formatKes(row.gross_sales) },
              { key: 'taxable_base', label: 'Taxable Base', align: 'right', render: (row) => formatKes(row.taxable_base) },
              { key: 'vat_collected', label: 'VAT Collected', align: 'right', render: (row) => formatKes(row.vat_collected) },
            ]}
            rows={data.by_tax_code}
            keyField="code"
            caption="VAT by tax code"
          />
        </>
      )}
    </div>
  );
}