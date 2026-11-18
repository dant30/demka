import { Link, useParams } from 'react-router-dom';
import { useAction, useDetail, useList } from '@/api/queries';
import { useState } from 'react';
import { endpoints } from '@/api/endpoints';
import { extractError } from '@/api/client';
import PageHeader from '@/components/ui/PageHeader';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Select from '@/components/ui/Select';
import Input from '@/components/ui/Input';

export default function RouteDetail() {
	const { id } = useParams();
	const { isBoss } = useAuth();
	const [showAssignCustomer, setShowAssignCustomer] = useState(false);
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
			<PageHeader
				title={route.name}
				description={route.code}
				backTo="/routes"
				backLabel="Routes"
				actions={<div className="flex items-center gap-2">
					<span className={`rounded px-2 py-1 text-sm ${route.is_active ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
						{route.is_active ? 'Active' : 'Inactive'}
					</span>
						{isBoss && route.is_active && (
							<Button variant="secondary" onClick={() => setShowAssignCustomer(true)}>
								Assign Customer
							</Button>
						)}
					{isBoss && <Link to={`/routes/${id}/edit`} className="btn-secondary">Edit Route</Link>}
				</div>}
			/>

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
			<AssignCustomerModal
				open={showAssignCustomer}
				onClose={() => setShowAssignCustomer(false)}
				routeId={id}
				routeName={route.name}
			/>
		</div>
	);
}

function AssignCustomerModal({ open, onClose, routeId, routeName }) {
	const [customerId, setCustomerId] = useState('');
	const [reason, setReason] = useState('');
	const [error, setError] = useState('');
	const { data, isLoading } = useList(
		'route-assignable-customers',
		endpoints.customers.list,
		{ is_active: true, page_size: 250 },
		{ enabled: open },
	);
	const customers = (data?.results || data || []).filter(
		(customer) => customer.customer_type !== 'WALK_IN',
	);
	const assign = useAction('assign-route-customer', endpoints.customers.assignRoute, {
		invalidate: ['customer', 'route-assignments', 'route', 'routes'],
		onSuccess: () => {
			setCustomerId('');
			setReason('');
			setError('');
			onClose();
		},
	});

	const submit = async () => {
		if (!customerId) {
			setError('Choose a customer first.');
			return;
		}
		setError('');
		try {
			await assign.mutateAsync({
				id: Number(customerId),
				route: Number(routeId),
				reason,
			});
		} catch (requestError) {
			setError(extractError(requestError, 'Could not assign customer.'));
		}
	};

	return (
		<Modal
			open={open}
			onClose={onClose}
			title={`Assign Customer to ${routeName}`}
			footer={(
				<>
					<Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
					<Button type="button" onClick={submit} loading={assign.isPending} disabled={!customers.length}>
						Assign Customer
					</Button>
				</>
			)}
		>
			<div className="space-y-4">
				<p className="text-sm text-slate-600">Assigning a customer here moves them from any currently assigned route.</p>
				<Select
					label="Customer"
					value={customerId}
					onChange={setCustomerId}
					disabled={isLoading || !customers.length}
					searchable
					options={[
						{ value: '', label: isLoading ? 'Loading customers...' : 'Select a customer...' },
						...customers.map((customer) => ({
							value: customer.id,
							label: customer.name,
							sublabel: customer.code,
						})),
					]}
				/>
				<Input label="Reason (optional)" value={reason} onChange={(event) => setReason(event.target.value)} />
				{!isLoading && !customers.length && <p className="text-sm text-slate-500">No active customers are available.</p>}
				{error && <div role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
			</div>
		</Modal>
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
