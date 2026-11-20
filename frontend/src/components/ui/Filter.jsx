import { useId, useState } from 'react';

export default function Filter({
	children,
	title = 'Filters',
	defaultExpanded = false,
	expanded: controlledExpanded,
	onExpandedChange,
	activeCount = 0,
	onClear,
	showClear = false,
	collapsible = true,
	headerContent,
	className = '',
	headerClassName = '',
	contentClassName = '',
}) {
	const panelId = useId();
	const titleId = useId();
	const [internalExpanded, setInternalExpanded] = useState(defaultExpanded);
	const isControlled = controlledExpanded !== undefined;
	const expanded = !collapsible || (isControlled ? controlledExpanded : internalExpanded);

	const toggleExpanded = () => {
		if (!collapsible) return;

		const nextValue = !expanded;
		if (!isControlled) setInternalExpanded(nextValue);
		onExpandedChange?.(nextValue);
	};

	return (
			<section className={`overflow-visible rounded-xl border border-slate-200 bg-white shadow-sm transition-shadow dark:border-slate-700 dark:bg-slate-900 ${className}`.trim()}>
			<div className={`flex min-h-12 items-center justify-between gap-3 px-3 py-2 sm:px-4 ${headerClassName}`.trim()}>
				<div className="flex min-w-0 flex-1 items-center gap-2">
					{headerContent ? (
						<>
							<h2 id={titleId} className="sr-only">{title}</h2>
							<div className="min-w-0 flex-1">{headerContent}</div>
						</>
					) : (
						<h2 id={titleId} className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">
							{title}
						</h2>
					)}
					{activeCount > 0 && (
						<span
							className="inline-flex min-w-5 items-center justify-center rounded-full bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-950 dark:text-brand-300"
							aria-label={`${activeCount} active filters`}
						>
							{activeCount}
						</span>
					)}
				</div>

				<div className="flex shrink-0 items-center gap-1">
					{showClear && onClear && activeCount > 0 && (
						<button
							type="button"
							onClick={onClear}
							className="min-h-9 rounded-md px-2 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
						>
							Clear all
						</button>
					)}

					{collapsible && (
						<button
							type="button"
							aria-expanded={expanded}
							aria-controls={panelId}
							aria-label={`${expanded ? 'Collapse' : 'Expand'} ${title.toLowerCase()}`}
							onClick={toggleExpanded}
							className="inline-flex min-h-9 min-w-9 items-center justify-center gap-1 rounded-md px-2 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
						>
							<span className="sr-only">
								{expanded ? 'Collapse filters' : 'Expand filters'}
							</span>
							<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
								<path d="M4 5h16l-6.2 7.1v5.1l-3.6 1.8v-6.9L4 5Z" />
							</svg>
							<svg
								aria-hidden="true"
								viewBox="0 0 20 20"
								fill="none"
								className={`h-4 w-4 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
								stroke="currentColor"
								strokeWidth="1.8"
								strokeLinecap="round"
								strokeLinejoin="round"
							>
								<path d="m5 7.5 5 5 5-5" />
							</svg>
						</button>
					)}
				</div>
			</div>
			<div
				id={panelId}
				role="region"
				aria-labelledby={titleId}
				hidden={!expanded}
				style={{ display: expanded ? undefined : 'none' }}
				className={`border-t border-slate-200 p-3 sm:p-4 dark:border-slate-700 ${contentClassName}`.trim()}
			>
				{children}
			</div>
		</section>
	);
}
