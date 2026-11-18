import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useDetail } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { useBluetoothPrinter } from '@/hooks/useBluetoothPrinter';
import { formatKes } from '@/utils/money';
import Button from '@/components/ui/Button';

export default function FieldSaleReceipt() {
  const { saleId } = useParams();
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('receiptJob');
  const navigate = useNavigate();
  const { data: sale } = useDetail('sale', endpoints.sales.detail(saleId), saleId);
  const bt = useBluetoothPrinter();

  return (
    <div className="w-full max-w-2xl space-y-4">
      <div className="card bg-green-50 border-green-200 text-center py-6">
        <div className="text-4xl mb-2">✓</div>
        <h1 className="text-xl font-bold text-green-900">Sale Complete</h1>
        {sale && <p className="text-sm text-green-800 mt-1">{sale.sale_number}</p>}
      </div>

      {sale && (
        <div className="card">
          <div className="space-y-1.5 text-sm">
            <Row label="Total" value={formatKes(sale.total)} />
            <Row label="Paid" value={formatKes(sale.amount_paid)} />
            {Number(sale.balance_due) > 0 && (
              <Row label="Balance" value={formatKes(sale.balance_due)} danger />
            )}
          </div>
        </div>
      )}

      {bt.supported ? (
        <Button
          onClick={() => bt.printJob(jobId)}
          loading={bt.busy}
          className="w-full"
          size="lg"
        >
          📱 Print Receipt via Bluetooth
        </Button>
      ) : (
        <div className="card text-sm text-slate-500">
          Bluetooth printing requires Chrome on Android.
        </div>
      )}

      {bt.error && <div className="text-sm text-red-600">{bt.error}</div>}

      <div className="grid grid-cols-2 gap-2">
        <Button variant="secondary" onClick={() => navigate('/field/sale/' + sale?.route)}>
          New Sale
        </Button>
        <Button variant="secondary" onClick={() => navigate('/field')}>
          Back to Run
        </Button>
      </div>
    </div>
  );
}

const Row = ({ label, value, danger }) => (
  <div className={`flex justify-between ${danger ? 'text-red-600 font-semibold' : ''}`}>
    <span className="text-slate-500">{label}</span>
    <span>{value}</span>
  </div>
);