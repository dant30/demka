
import { useId } from 'react';

const variants = {
    primary: 'bg-brand-600',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
    info: 'bg-sky-500',
    neutral: 'bg-slate-500',
};

const sizes = {
    xs: 'h-1',
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
    xl: 'h-4',
};

export default function ProgressBar({
    value = 0,
    max = 100,
    min = 0,
    label,
    showValue = false,
    showPercentage = true,
    variant = 'primary',
    size = 'md',
    rounded = 'full',
    striped = false,
    animated = true,
    indeterminate = false,
    className = '',
    barClassName = '',
    labelClassName = '',
    helperText,
    valueLabel,
    id,
}) {
    const generatedId = useId();
    const progressId = id || generatedId;

    const safeMax = Number.isFinite(max) ? max : 100;
    const safeMin = Number.isFinite(min) ? min : 0;
    const safeValue = Number.isFinite(value) ? value : safeMin;

    const range = Math.max(0, safeMax - safeMin);
    const percentage = range > 0
        ? Math.min(100, Math.max(0, ((safeValue - safeMin) / range) * 100))
        : 0;

    const roundedPercentage = Math.round(percentage);

    const progressColor = variants[variant] || variants.primary;
    const progressSize = sizes[size] || sizes.md;

    const radius = rounded === 'none'
        ? 'rounded-none'
        : rounded === 'md'
            ? 'rounded-md'
            : 'rounded-full';

    const formattedValue = valueLabel ?? (
        showPercentage
            ? `${roundedPercentage}%`
            : `${safeValue} / ${safeMax}`
    );

    return (
        <div className={`w-full ${className}`.trim()}>
            {(label || showValue || helperText) && (
                <div className="mb-2 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                        {label && (
                            <label
                                htmlFor={progressId}
                                className={`block truncate text-sm font-medium text-slate-700 dark:text-slate-200 ${labelClassName}`}
                            >
                                {label}
                            </label>
                        )}

                        {helperText && (
                            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                                {helperText}
                            </p>
                        )}
                    </div>

                    {showValue && (
                        <span className="shrink-0 text-sm font-semibold tabular-nums text-slate-700 dark:text-slate-200">
                            {formattedValue}
                        </span>
                    )}
                </div>
            )}

            <div
                id={progressId}
                role="progressbar"
                aria-label={label || 'Progress'}
                aria-valuemin={indeterminate ? undefined : safeMin}
                aria-valuemax={indeterminate ? undefined : safeMax}
                aria-valuenow={indeterminate ? undefined : safeValue}
                aria-valuetext={indeterminate ? 'In progress' : formattedValue}
                className={`relative w-full overflow-hidden bg-slate-100 dark:bg-slate-800 ${progressSize} ${radius}`}
            >
                <div
                    className={[
                        'h-full',
                        progressColor,
                        radius,
                        striped ? 'progress-striped' : '',
                        indeterminate
                            ? 'progress-indeterminate'
                            : animated
                                ? 'transition-[width] duration-500 ease-out'
                                : '',
                        barClassName,
                    ].filter(Boolean).join(' ')}
                    style={{
                        width: indeterminate ? '35%' : `${percentage}%`,
                    }}
                />
            </div>
        </div>
    );
}
