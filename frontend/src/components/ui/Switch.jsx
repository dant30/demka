import { forwardRef, useId } from 'react';

const Switch = forwardRef(function Switch({
	label,
	description,
	className = '',
	id,
	...props
}, ref) {
	const generatedId = useId();
	const fieldId = id || generatedId;

	return (
		<label className={`switch-field ${props.disabled ? 'switch-field--disabled' : ''} ${className}`}>
			<span className="min-w-0">
				{label && <span className="block text-sm font-medium text-slate-700">{label}</span>}
				{description && <span className="block text-xs text-slate-500">{description}</span>}
			</span>
			<input {...props} ref={ref} id={fieldId} type="checkbox" role="switch" className="switch-input" />
			<span className="switch-track" aria-hidden="true"><span className="switch-thumb" /></span>
		</label>
	);
});

export default Switch;
