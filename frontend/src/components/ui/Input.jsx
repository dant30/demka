import { forwardRef, useId } from 'react';

const Input = forwardRef(function Input(
  { label, error, hint, className = '', id, ...props }, ref
) {
  const generatedId = useId();
  const fieldId = id || generatedId;

  return (
    <div className={className}>
      {label && <label className="label" htmlFor={fieldId}>{label}</label>}
      <input
        ref={ref}
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
});

export default Input;