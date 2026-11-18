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
  return new Date().toISOString().slice(0, 10);
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