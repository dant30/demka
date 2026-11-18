import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { formatKes } from '@/utils/money';
import { formatDate } from '@/utils/dates';
import DataTable from '@/components/ui/DataTable';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import DatePicker from '@/components/ui/DatePicker';
import PageHeader from '@/components/ui/PageHeader';
import Filter from '@/components/ui/Filter';
import { useCreate, useList, useAction } from '@/api/queries';
import ChartPanel from '@/components/charts/ChartPanel';
import TrendChart from '@/components/charts/TrendChart';

export default function ExpensesList() {
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [period, setPeriod] = useState('monthly');

  const { data, isLoading, refetch } = useList('expenses', endpoints.expenses.list, {
    page, category: categoryFilter || undefined, page_size: 25,
  });
  const { data: categories } = useList('expense-categories', endpoints.expenses.categories);
  const { data: trend } = useQuery({
    queryKey: ['expenses-trend'],
    queryFn: async () => (await api.get(endpoints.expenses.monthlyTrend, {
      params: { months: 6 },
    })).data,
  });
  const { data: summary } = useQuery({
    queryKey: ['expenses-summary', period],
    queryFn: async () => (await api.get(endpoints.expenses.summary, {
      params: { period },
    })).data,
  });

  const rows = data?.results || [];
  const totalPages = data ? Math.ceil(data.count / 25) : 0;

  const columns = [
    { key: 'expense_number', label: 'Expense #' },
    { key: 'expense_date', label: 'Date', render: (r) => formatDate(r.expense_date) },
    { key: 'category_name', label: 'Category' },
    { key: 'amount', label: 'Amount', align: 'right', render: (r) => formatKes(r.amount) },
    { key: 'description', label: 'Description', render: (r) => r.description?.slice(0, 40) || '—' },
    { key: 'payment_method_code', label: 'Method' },
    { key: 'location_name', label: 'Location', render: (r) => r.location_name || '—' },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Expenses"
        description="Review spending, category totals, and monthly trends."
        actions={<Button onClick={() => setCreateOpen(true)}>+ New Expense</Button>}
      />

      {summary && (
        <div className="card">
          <h3 className="font-semibold mb-3">Total — {period}</h3>
          <div className="text-3xl font-bold mb-4">{formatKes(summary.total)}</div>
          <div className="space-y-1">
            {summary.by_category?.map((c) => (
              <div key={c.category_id} className="flex justify-between text-sm">
                <span>{c.category}</span>
                <span className="font-medium">{formatKes(c.total)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {trend && (
        <ChartPanel title="Monthly Trend" description="Expense totals by month">
          <TrendChart
            data={trend}
            xKey="label"
            type="bar"
            series={[{ dataKey: 'total', name: 'Expenses', color: '#d97706' }]}
            valueFormatter={formatKes}
            height={240}
          />
        </ChartPanel>
      )}

      <Filter title="Expense filters" contentClassName="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="">All categories</option>
          {(categories || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </Select>
        <Select value={period} onChange={(e) => setPeriod(e.target.value)}>
          <option value="daily">Today</option>
          <option value="weekly">This week</option>
          <option value="monthly">This month</option>
          <option value="quarterly">This quarter</option>
          <option value="yearly">This year</option>
        </Select>
      </Filter>

      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Pagination page={page} totalPages={totalPages} onChange={setPage} />

      <CreateExpenseModal
        open={createOpen}
        categories={categories || []}
        onClose={() => setCreateOpen(false)}
        onSuccess={() => { setCreateOpen(false); refetch(); }}
      />
    </div>
  );
}

function CreateExpenseModal({ open, onClose, categories, onSuccess }) {
  const [form, setForm] = useState({
    category: '', amount: '', description: '',
    expense_date: new Date().toISOString().slice(0, 10),
    payment_method: '', reference: '',
  });
  const { data: methods } = useList('payment-methods', endpoints.payments.methods);
  const [file, setFile] = useState(null);
  const create = useCreate('expenses', endpoints.expenses.list, { onSuccess });

  const submit = async () => {
    const payload = { ...form };
    // multipart for file upload
    const body = file ? new FormData() : payload;
    if (file) {
      Object.entries(payload).forEach(([k, v]) => body.append(k, v));
      body.append('receipt_image', file);
    }
    await create.mutateAsync(body);
  };

  const set = (k, v) => setForm({ ...form, [k]: v });

  return (
    <Modal open={open} onClose={onClose} title="New Expense" size="lg">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Select label="Category" value={form.category} onChange={(e) => set('category', e.target.value)}>
          <option value="">Select...</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </Select>
        <Input label="Amount" type="number" step="0.01" value={form.amount} onChange={(e) => set('amount', e.target.value)} />
        <DatePicker label="Date" value={form.expense_date} onChange={(value) => set('expense_date', value)} />
        <Select label="Payment Method" value={form.payment_method} onChange={(e) => set('payment_method', e.target.value)}>
          <option value="">Select...</option>
          {(methods || []).map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </Select>
        <div className="md:col-span-2">
          <Input label="Description" value={form.description} onChange={(e) => set('description', e.target.value)} />
        </div>
        <div className="md:col-span-2">
          <label className="label">Receipt Image (optional)</label>
          <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0])} className="input" />
        </div>
      </div>
      <Button onClick={submit} loading={create.isPending} className="w-full mt-4">Create Expense</Button>
    </Modal>
  );
}

import Pagination from '@/components/ui/Pagination';