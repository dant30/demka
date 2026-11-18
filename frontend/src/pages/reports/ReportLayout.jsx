import { useSearchParams } from 'react-router-dom';
import { PERIODS } from '@/utils/dates';
import PageHeader from '@/components/ui/PageHeader';
import DatePicker from '@/components/ui/DatePicker';
import Select from '@/components/ui/Select';

export function PeriodSelector() {
  const [searchParams, setSearchParams] = useSearchParams();
  const period = searchParams.get('period') || 'monthly';
  const start = searchParams.get('start') || '';
  const end = searchParams.get('end') || '';

  const setParam = (k, v) => {
    const next = new URLSearchParams(searchParams);
    if (v) next.set(k, v);
    else next.delete(k);
    setSearchParams(next);
  };

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <Select
        aria-label="Report period"
        className="w-full sm:max-w-[160px]"
        value={period}
        onChange={(e) => setParam('period', e.target.value)}
      >
        {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
      </Select>
      <DatePicker
        aria-label="Start date"
        className="w-full sm:max-w-[160px]"
        value={start}
        onChange={(value) => setParam('start', value)}
      />
      <span>—</span>
      <DatePicker
        aria-label="End date"
        className="w-full sm:max-w-[160px]"
        value={end}
        onChange={(value) => setParam('end', value)}
      />
      <a
        href={`?${searchParams.toString()}&format=csv`}
        className="btn-secondary text-sm"
      >
        CSV
      </a>
    </div>
  );
}

export function ReportHeader({ title, description }) {
  return (
    <PageHeader title={title} description={description} actions={<PeriodSelector />} />
  );
}