import { useId } from 'react';

export default function TextareaField({
  label,
  error,
  hint,
  className = '',
  id,
  ...props
}) {
  const generatedId = useId();
  const fieldId = id || generatedId;

  return (
    <div className={className}>
      {label && <label className="label" htmlFor={fieldId}>{label}</label>}
      <textarea
        id={fieldId}
        className={`input ${error ? 'input-error' : ''}`}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={error ? `${fieldId}-error` : hint ? `${fieldId}-hint` : undefined}
        {...props}
      />
      {error && <p id={`${fieldId}-error`} className="field-error">{error}</p>}
      {hint && !error && <p id={`${fieldId}-hint`} className="field-hint">{hint}</p>}
    </div>
  );
}
