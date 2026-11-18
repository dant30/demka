import { useState } from 'react';
import Button from './Button';
import Modal from './Modal';

export default function ConfirmDialong({
	open,
	onClose,
	onConfirm,
	title = 'Confirm action',
	description,
	confirmLabel = 'Confirm',
	cancelLabel = 'Cancel',
	variant = 'danger',
	loading = false,
	error,
}) {
	const [confirmError, setConfirmError] = useState('');

	const confirm = async () => {
		setConfirmError('');
		try {
			await onConfirm?.();
			onClose?.();
		} catch (reason) {
			setConfirmError(reason?.message || 'The action could not be completed.');
		}
	};

	return (
		<Modal
			open={open}
			onClose={onClose}
			title={title}
			size="sm"
			footer={(
				<>
					<Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
						{cancelLabel}
					</Button>
					<Button type="button" variant={variant} onClick={confirm} loading={loading}>
						{confirmLabel}
					</Button>
				</>
			)}
		>
			{description && <p className="text-sm leading-6 text-slate-600">{description}</p>}
			{(error || confirmError) && (
				<p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
					{error || confirmError}
				</p>
			)}
		</Modal>
	);
}
