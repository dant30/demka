import { forwardRef, useId } from 'react';

const CheckBox = forwardRef(function CheckBox({
	label,
	description,
	error,
	className = '',
	id,
	...props
}, ref) {
	const generatedId = useId();
	const fieldId = id || generatedId;

	return (
		<div className={className}>
			<label htmlFor={fieldId} className={`checkbox-field ${props.disabled ? 'checkbox-field--disabled' : ''}`}>
				<input
					{...props}
					ref={ref}
					id={fieldId}
					type="checkbox"
					aria-invalid={error ? 'true' : undefined}
					aria-describedby={error ? `${fieldId}-error` : description ? `${fieldId}-description` : undefined}
					className="checkbox-control"
				/>
				{(label || description) && (
					<span className="min-w-0">
						{label && <span className="block text-sm font-medium text-slate-700">{label}</span>}
						{description && <span id={`${fieldId}-description`} className="block text-xs text-slate-500">{description}</span>}
					</span>
				)}
			</label>
			{error && <p id={`${fieldId}-error`} className="field-error">{error}</p>}
		</div>
	);
});

export default CheckBox;
