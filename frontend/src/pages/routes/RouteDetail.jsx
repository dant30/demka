import { Link, useParams } from 'react-router-dom';
import { useDetail, useList } from '@/api/queries';
import { endpoints } from '@/api/endpoints';

export default function RouteDetail() {
	const { id } = useParams();
	const { data: route, isLoading, isError } = useDetail(
		'route',
		id ? endpoints.routes.detail(id) : null,
		id,
	);
	const { data: runsData, isLoading: runsLoading } = useList(
		'route-runs',
		id ? endpoints.routes.routeRuns(id) : null,
	);
	const runs = Array.isArray(runsData) ? runsData : runsData?.results || [];

	if (isLoading) return <p className="text-slate-500">Loading route...</p>;
	if (isError || !route) return <p className="text-red-600">Could not load this route.</p>;

	return (
		<div className="space-y-6 max-w-5xl">
			<div className="flex flex-wrap items-start justify-between gap-3">
				<div>
					<Link to="/routes" className="text-sm text-brand-600 hover:underline">← Routes</Link>
					<h1 className="mt-2 text-2xl font-bold">{route.name}</h1>
					<p className="text-sm text-slate-500">{route.code}</p>
				</div>
				<span className={`rounded px-2 py-1 text-sm ${route.is_active ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
					{route.is_active ? 'Active' : 'Inactive'}
				</span>
			</div>

			<div className="card grid grid-cols-1 gap-4 sm:grid-cols-3">
				<Info label="Default agent" value={route.default_agent_name || '—'} />
				<Info label="Schedule" value={formatDays(route.schedule_days)} />
				<Info label="Assigned customers" value={route.customer_count ?? '—'} />
				{route.description && <Info label="Description" value={route.description} />}
			</div>

			<section className="card p-0">
				<div className="p-4 border-b border-slate-200">
					<h2 className="font-semibold">Recent Runs</h2>
				</div>
				{runsLoading ? (
					<p className="p-4 text-sm text-slate-500">Loading runs...</p>
				) : runs.length === 0 ? (
					<p className="p-4 text-sm text-slate-500">No runs found.</p>
				) : (
					<div className="overflow-x-auto">
						<table className="table">
							<thead><tr><th>Date</th><th>Agent</th><th>Status</th><th /></tr></thead>
							<tbody>
								{runs.map((run) => (
									<tr key={run.id}>
										<td>{run.run_date || '—'}</td>
										<td>{run.agent_name || '—'}</td>
										<td>{run.status_display || run.status || '—'}</td>
										<td className="text-right">
											<Link to={`/routes/runs/${run.id}`} className="text-brand-600 hover:underline">View</Link>
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				)}
			</section>
		</div>
	);
}

function Info({ label, value }) {
	return (
		<div>
			<div className="text-xs uppercase text-slate-500">{label}</div>
			<div className="mt-1 font-medium">{value}</div>
		</div>
	);
}

function formatDays(days) {
	if (!days?.length) return '—';
	const names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
	return days.map((day) => names[day] ?? day).join(', ');
}
