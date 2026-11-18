export function formatDate(value) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleDateString('en-KE', {
      year: 'numeric', month: 'short', day: 'numeric',
    });
  } catch {
    return '—';
  }
}

export function formatDateTime(value) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleString('en-KE', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return '—';
  }
}

export function todayIso() {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'Africa/Nairobi',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const part = (type) => parts.find((value) => value.type === type)?.value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}

export function isoDate(d) {
  return new Date(d).toISOString().slice(0, 10);
}

export const PERIODS = [
  { value: 'daily',     label: 'Today' },
  { value: 'weekly',    label: 'This week' },
  { value: 'monthly',   label: 'This month' },
  { value: 'quarterly', label: 'This quarter' },
  { value: 'yearly',    label: 'This year' },
];