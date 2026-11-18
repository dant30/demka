const VARIANTS = {
	neutral: 'badge-neutral',
	brand: 'badge-brand',
	success: 'badge-success',
	warning: 'badge-warning',
	danger: 'badge-danger',
};

export default function Badge({
	children,
	variant = 'neutral',
	dot = false,
	className = '',
	...props
}) {
	return (
		<span className={`${VARIANTS[variant] || VARIANTS.neutral} ${className}`} {...props}>
			{dot && <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />}
			{children}
		</span>
	);
}
