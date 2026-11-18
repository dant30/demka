export default function ChartPanel({ title, description, actions, children, className = '' }) {
  return (
    <section className={`chart-panel ${className}`}>
      {(title || description || actions) && (
        <header className="chart-panel-header">
          <div className="min-w-0">
            {title && <h2 className="chart-panel-title">{title}</h2>}
            {description && <p className="chart-panel-description">{description}</p>}
          </div>
          {actions && <div className="chart-panel-actions">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}
