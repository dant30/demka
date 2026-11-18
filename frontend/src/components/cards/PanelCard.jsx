export default function PanelCard({
  title,
  description,
  actions,
  children,
  className = '',
  contentClassName = '',
}) {
  return (
    <section className={`panel-card ${className}`}>
      {(title || description || actions) && (
        <header className="panel-card-header">
          <div className="min-w-0">
            {title && <h2 className="panel-card-title">{title}</h2>}
            {description && <p className="panel-card-description">{description}</p>}
          </div>
          {actions && <div className="panel-card-actions">{actions}</div>}
        </header>
      )}
      <div className={contentClassName}>{children}</div>
    </section>
  );
}
