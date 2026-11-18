import { useParams, useNavigate } from 'react-router-dom';
import { useDetail, useAction } from '@/api/queries';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDateTime } from '@/utils/dates';
import Button from '@/components/ui/Button';

export default function RouteRunDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: run } = useDetail('run', endpoints.routes.runDetail(id), id);
  const { data: recon } = useDetail('run-recon', endpoints.routes.runReconciliation(id), id);

  if (!run) return <div>Loading...</div>;

  return (
    <div className="w-full min-w-0 space-y-6">
      <div className="flex justify-between">
        <div>
          <h1 className="text-2xl font-bold">{run.route_name}</h1>
          <p className="text-sm text-slate-500">
            {formatDateTime(run.run_date)} · {run.agent_name} · {run.stock_location_name}
          </p>
        </div>
        <Button variant="secondary" onClick={() => navigate(`/routes/${run.route}`)}>
          View Route
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Status" value={run.status_display} />
        <Stat label="Cash Collected" value={formatKes(run.cash_collected)} />
        <Stat label="Cash Expected" value={run.cash_expected ? formatKes(run.cash_expected) : '—'} />
        <Stat label="Cash Variance"
          value={run.cash_variance ? formatKes(run.cash_variance) : '—'}
          danger={run.cash_variance && Number(run.cash_variance) !== 0}
        />
      </div>

      {recon && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card">
            <h3 className="font-semibold mb-2">Sales</h3>
            <div className="space-y-1 text-sm">
              <Row label="Count" value={recon.sales.count} />
              <Row label="Revenue" value={formatKes(recon.sales.total)} />
              <Row label="COGS" value={formatKes(recon.sales.cogs)} />
              <Row label="Gross" value={formatKes(recon.sales.gross_profit)} bold />
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold mb-2">Expenses</h3>
            <div className="space-y-1 text-sm">
              <Row label="Total" value={formatKes(recon.expenses.total)} bold />
              {recon.expenses.by_category?.slice(0, 4).map((c) => (
                <Row key={c.category_id} label={c.category} value={formatKes(c.total)} />
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold mb-2">Profit</h3>
            <div className="space-y-1 text-sm">
              <Row label="Gross" value={formatKes(recon.profit.gross)} />
              <Row label="Net" value={formatKes(recon.profit.net)} bold />
            </div>
            <h4 className="font-semibold mt-3 mb-1">Stock</h4>
            <div className="space-y-1 text-sm">
              <Row label="Opening" value={formatKes(recon.stock.opening_value)} />
              <Row label="Closing" value={formatKes(recon.stock.closing_value)} />
              <Row label="Variance" value={formatKes(recon.stock.variance)}
                danger={Number(recon.stock.variance) < 0} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const Stat = ({ label, value, danger }) => (
  <div className="card">
    <div className="text-xs text-slate-500 uppercase">{label}</div>
    <div className={`mt-1 font-semibold ${danger ? 'text-red-600' : ''}`}>{value}</div>
  </div>
);
const Row = ({ label, value, bold, danger }) => (
  <div className={`flex justify-between ${bold ? 'font-semibold' : ''} ${danger ? 'text-red-600' : ''}`}>
    <span className="text-slate-500">{label}</span><span>{value}</span>
  </div>
);