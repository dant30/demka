export default function FormSection({
  title,
  description,
  columns = 2,
  children,
  className = '',
}) {
  const columnClass = columns === 3 ? 'form-grid--three' : columns === 1 ? 'form-grid--one' : 'form-grid--two';

  return (
    <section className={`form-section ${className}`}>
      {(title || description) && (
        <header className="form-section-header">
          <div>
            {title && <h2 className="form-section-title">{title}</h2>}
            {description && <p className="form-section-description">{description}</p>}
          </div>
        </header>
      )}
      <div className={`form-grid ${columnClass}`}>{children}</div>
    </section>
  );
}
