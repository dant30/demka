import { Link } from 'react-router-dom';
import PageHeader from '@/components/ui/PageHeader';

const REPORTS = [
  { to: '/reports/profit-loss', label: 'Profit & Loss', icon: '📊', desc: 'Revenue, COGS, expenses, net profit' },
  { to: '/reports/sales', label: 'Sales Analysis', icon: '💰', desc: 'By day, channel, customer type, top products' },
  { to: '/reports/cash', label: 'Cash & Payments', icon: '💳', desc: 'Daily reconciliation, method breakdown' },
  { to: '/reports/vat', label: 'VAT Summary', icon: '🏛️', desc: 'KRA-ready tax summary' },
  { to: '/reports/stock', label: 'Stock', icon: '📦', desc: 'Valuation, low stock, dead stock' },
  { to: '/reports/customers', label: 'Customers', icon: '👥', desc: 'Aging, top customers, credit utilization' },
  { to: '/reports/suppliers', label: 'Suppliers', icon: '🚚', desc: 'Purchases, price trends' },
  { to: '/reports/etims', label: 'eTIMS Health', icon: '✅', desc: 'Submission success, failures' },
  { to: '/reports/route-performance', label: 'Field Performance', icon: '🚐', desc: 'Agent runs, sales, and cash variance' },
  { to: '/reports/expenses', label: 'Expenses', icon: '💸', desc: 'Spend by period, category, location, and trend' },
];

export default function ReportsHome() {
  return (
    <div className="space-y-6">
      <PageHeader title="Reports" description="Operational, financial, and compliance reporting." />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {REPORTS.map((r) => (
          <Link key={r.to} to={r.to} className="card hover:border-brand-500 hover:shadow-md transition">
            <div className="text-3xl mb-2">{r.icon}</div>
            <h3 className="font-semibold">{r.label}</h3>
            <p className="text-sm text-slate-500 mt-1">{r.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}