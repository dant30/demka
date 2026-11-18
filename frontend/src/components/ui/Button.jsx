export default function Button({
  children, variant = 'primary', size = 'md',
  loading = false, loadingText, disabled = false, className = '', ...props
}) {
  const variants = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    danger: 'btn-danger',
    ghost: 'btn-ghost',
  };
  const sizes = { sm: 'px-3 py-1.5 text-sm', md: '', lg: 'btn-lg' };

  return (
    <button
      className={`${variants[variant] || variants.primary} ${sizes[size] || ''} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && (
        <svg aria-hidden="true" className="animate-spin h-4 w-4" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      )}
      {loading && loadingText ? loadingText : children}
    </button>
  );
}