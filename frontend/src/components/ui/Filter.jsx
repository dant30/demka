import { useId, useState } from 'react';

export default function Filter({
	children,
	title = 'Filters',
	defaultExpanded = true,
	className = '',
	contentClassName = '',
}) {
	const panelId = useId();
	const [expanded, setExpanded] = useState(defaultExpanded);

	return (
		<section className={`overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm ${className}`.trim()}>
			<div className="flex min-h-11 items-center justify-between px-3 py-2">
				<h2 className="text-sm font-semibold text-slate-800">{title}</h2>
				<button
					type="button"
					aria-expanded={expanded}
					aria-controls={panelId}
					aria-label={`${expanded ? 'Hide' : 'Show'} ${title.toLowerCase()}`}
					title={`${expanded ? 'Hide' : 'Show'} ${title.toLowerCase()}`}
					onClick={() => setExpanded((current) => !current)}
					className="inline-flex min-h-8 items-center gap-1 rounded-md px-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
				>
					<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
						<path d="M4 5h16l-6.2 7.1v5.1l-3.6 1.8v-6.9L4 5Z" />
					</svg>
					<svg aria-hidden="true" viewBox="0 0 20 20" fill="none" className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
						<path d="m5 7.5 5 5 5-5" />
					</svg>
				</button>
			</div>
			<div
				id={panelId}
				hidden={!expanded}
				className={`border-t border-slate-200 p-3 ${contentClassName}`.trim()}
			>
				{children}
			</div>
		</section>
	);
}
