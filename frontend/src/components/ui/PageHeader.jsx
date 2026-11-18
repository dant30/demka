import { Link } from 'react-router-dom';

export default function PageHeader({
	title,
	description,
	eyebrow,
	actions,
	backTo,
	backLabel = 'Back',
	className = '',
}) {
	return (
		<header className={`page-header ${className}`}>
			<div className="min-w-0 flex-1">
				{backTo && (
					<Link to={backTo} className="page-header-back">
						<span aria-hidden="true">←</span> {backLabel}
					</Link>
				)}
				{eyebrow && <p className="page-header-eyebrow">{eyebrow}</p>}
				<h1 className="page-title">{title}</h1>
				{description && <p className="page-header-description">{description}</p>}
			</div>
			{actions && <div className="page-header-actions">{actions}</div>}
		</header>
	);
}
