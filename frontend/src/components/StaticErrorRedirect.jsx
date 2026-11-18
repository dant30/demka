import { useEffect } from 'react';

export default function StaticErrorRedirect({ path }) {
	useEffect(() => {
		window.location.replace(path);
	}, [path]);

	return (
		<main className="mx-auto max-w-xl px-4 py-12 text-center">
			<p className="text-sm text-slate-600" role="status">Opening the requested status page...</p>
			<a className="mt-3 inline-flex text-sm font-medium text-brand-700 hover:underline" href={path}>
				Continue
			</a>
		</main>
	);
}