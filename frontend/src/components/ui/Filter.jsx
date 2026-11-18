import { useEffect, useId, useState } from 'react';

export default function Filter({
	children,
	title = 'Filters',
	defaultExpanded = true,
	collapsibleOnMobile = false,
	className = '',
	contentClassName = '',
}) {
	const panelId = useId();
	const [expanded, setExpanded] = useState(() => (
		collapsibleOnMobile
			? window.matchMedia('(min-width: 640px)').matches
			: defaultExpanded
	));

	useEffect(() => {
		if (!collapsibleOnMobile) return undefined;
		const breakpoint = window.matchMedia('(min-width: 640px)');
		const syncExpanded = (event) => setExpanded(event.matches);
		breakpoint.addEventListener('change', syncExpanded);
		return () => breakpoint.removeEventListener('change', syncExpanded);
	}, [collapsibleOnMobile]);

	const sectionClassName = collapsibleOnMobile
		? `overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm sm:p-4 ${className}`
		: `overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm ${className}`;

	return (
		<section className={sectionClassName.trim()}>
			<div className={`flex min-h-11 items-center justify-between px-3 py-2 ${collapsibleOnMobile ? 'sm:hidden' : ''}`}>
				<h2 className="text-sm font-semibold text-slate-800">{title}</h2>
				<button
					type="button"
					aria-expanded={expanded}
					aria-controls={panelId}
					aria-label={`${expanded ? 'Hide' : 'Show'} ${title.toLowerCase()}`}
					title={`${expanded ? 'Hide' : 'Show'} ${title.toLowerCase()}`}
					onClick={() => setExpanded((current) => !current)}
					className={`inline-flex min-h-8 items-center gap-1 rounded-md px-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${collapsibleOnMobile ? 'sm:hidden' : ''}`}
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
				className={`border-t border-slate-200 p-3 ${collapsibleOnMobile ? 'sm:border-0 sm:p-0' : ''} ${contentClassName}`.trim()}
			>
				{children}
			</div>
		</section>
	);
}
