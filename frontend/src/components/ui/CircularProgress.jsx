
import { useId } from 'react';

const variants = {
    primary: {
        stroke: 'stroke-brand-600',
        text: 'text-brand-700 dark:text-brand-400',
    },
    success: {
        stroke: 'stroke-emerald-500',
        text: 'text-emerald-600 dark:text-emerald-400',
    },
    warning: {
        stroke: 'stroke-amber-500',
        text: 'text-amber-600 dark:text-amber-400',
    },
    danger: {
        stroke: 'stroke-rose-500',
        text: 'text-rose-600 dark:text-rose-400',
    },
    info: {
        stroke: 'stroke-sky-500',
        text: 'text-sky-600 dark:text-sky-400',
    },
    neutral: {
        stroke: 'stroke-slate-500',
        text: 'text-slate-600 dark:text-slate-400',
    },
};

const sizes = {
    xs: { size: 36, stroke: 3 },
    sm: { size: 48, stroke: 4 },
    md: { size: 64, stroke: 5 },
    lg: { size: 88, stroke: 7 },
    xl: { size: 112, stroke: 9 },
    '2xl': { size: 144, stroke: 11 },
};

export default function CircularProgress({
    value = 0,
    max = 100,
    min = 0,

    // Appearance
    size = 'md',
    variant = 'primary',
    strokeWidth,
    trackColor = 'stroke-slate-100 dark:stroke-slate-800',
    rounded = true,

    // Content
    showValue = true,
    showPercentage = true,
    label,
    description,
    valueLabel,
    centerContent,

    // Behavior
    animated = true,
    indeterminate = false,

    // Optional gradient
    gradient = false,
    gradientEndColor = '#60a5fa',

    // Styling
    className = '',
    svgClassName = '',

    // Accessibility
    ariaLabel,
}) {
    const gradientId = useId();

    const selectedSize = sizes[size] || sizes.md;
    const selectedVariant = variants[variant] || variants.primary;

    const dimension = selectedSize.size;
    const thickness = strokeWidth ?? selectedSize.stroke;

    const safeMin = Number.isFinite(min) ? min : 0;
    const safeMax = Number.isFinite(max) ? max : 100;
    const safeValue = Number.isFinite(value) ? value : safeMin;

    const range = Math.max(0, safeMax - safeMin);

    const percentage = range > 0
        ? Math.min(100, Math.max(0, ((safeValue - safeMin) / range) * 100))
        : 0;

    const radius = (dimension - thickness) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    const displayValue = valueLabel ?? (
        showPercentage
            ? `${Math.round(percentage)}%`
            : `${safeValue}/${safeMax}`
    );

    const strokeClass = gradient ? '' : selectedVariant.stroke;

    return (
        <div
            className={`inline-flex flex-col items-center gap-2 ${className}`.trim()}
        >
            <div
                className="relative inline-flex shrink-0 items-center justify-center"
                style={{
                    width: dimension,
                    height: dimension,
                }}
            >
                <svg
                    viewBox={`0 0 ${dimension} ${dimension}`}
                    className={`h-full w-full -rotate-90 ${svgClassName}`}
                    role="progressbar"
                    aria-label={ariaLabel || label || 'Progress'}
                    aria-valuemin={indeterminate ? undefined : safeMin}
                    aria-valuemax={indeterminate ? undefined : safeMax}
                    aria-valuenow={indeterminate ? undefined : safeValue}
                    aria-valuetext={
                        indeterminate ? 'In progress' : displayValue
                    }
                >
                    <defs>
                        {gradient && (
                            <linearGradient
                                id={gradientId}
                                x1="0%"
                                y1="0%"
                                x2="100%"
                                y2="100%"
                            >
                                <stop offset="0%" stopColor="#2563eb" />
                                <stop offset="100%" stopColor={gradientEndColor} />
                            </linearGradient>
                        )}
                    </defs>

                    {/* Background track */}
                    <circle
                        cx={dimension / 2}
                        cy={dimension / 2}
                        r={radius}
                        fill="none"
                        strokeWidth={thickness}
                        className={trackColor}
                    />

                    {/* Progress indicator */}
                    <circle
                        cx={dimension / 2}
                        cy={dimension / 2}
                        r={radius}
                        fill="none"
                        strokeWidth={thickness}
                        strokeLinecap={rounded ? 'round' : 'butt'}
                        stroke={gradient ? `url(#${gradientId})` : undefined}
                        className={[
                            strokeClass,
                            indeterminate
                                ? 'circular-progress-indeterminate'
                                : animated
                                    ? 'transition-[stroke-dashoffset] duration-700 ease-out'
                                    : '',
                        ].filter(Boolean).join(' ')}
                        strokeDasharray={
                            indeterminate
                                ? `${circumference * 0.25} ${circumference}`
                                : circumference
                        }
                        strokeDashoffset={
                            indeterminate
                                ? 0
                                : offset
                        }
                    />
                </svg>

                {/* Center content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                    {centerContent ?? (
                        <>
                            {showValue && (
                                <span
                                    className={[
                                        'font-bold leading-none tracking-tight tabular-nums',
                                        selectedVariant.text,
                                        dimension < 48
                                            ? 'text-[10px]'
                                            : dimension < 72
                                                ? 'text-sm'
                                                : dimension < 112
                                                    ? 'text-lg'
                                                    : 'text-2xl',
                                    ].join(' ')}
                                >
                                    {indeterminate ? '...' : displayValue}
                                </span>
                            )}

                            {label && dimension >= 64 && (
                                <span className="mt-1 max-w-[85%] truncate text-[9px] font-medium text-slate-500 dark:text-slate-400">
                                    {label}
                                </span>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* External label for smaller indicators */}
            {description && (
                <p className="max-w-32 text-center text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                    {description}
                </p>
            )}
        </div>
    );
}
