export function formatKes(value, { withSymbol = true } = {}) {
  if (value === null || value === undefined || value === '') return withSymbol ? 'KES 0.00' : '0.00';
  const n = Number(value);
  if (Number.isNaN(n)) return withSymbol ? 'KES 0.00' : '0.00';
  const formatted = n.toLocaleString('en-KE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return withSymbol ? `KES ${formatted}` : formatted;
}

export function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined) return '0';
  const n = Number(value);
  if (Number.isNaN(n)) return '0';
  return n.toLocaleString('en-KE', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}