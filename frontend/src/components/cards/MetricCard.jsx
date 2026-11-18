const ACCENTS = {
  brand: 'metric-card--brand',
  success: 'metric-card--success',
  warning: 'metric-card--warning',
  danger: 'metric-card--danger',
};

export default function MetricCard({ label, value, detail, accent = 'brand', className = '' }) {
  return (
    <section className={`metric-card ${ACCENTS[accent] || ACCENTS.brand} ${className}`}>
      <h2 className="metric-card-label">{label}</h2>
      <p className="metric-card-value">{value}</p>
      {detail && <p className="metric-card-detail">{detail}</p>}
    </section>
  );
}
