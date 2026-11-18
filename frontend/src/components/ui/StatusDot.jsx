const STATUS_STYLES = {
	healthy: { color: "bg-emerald-500", label: "Healthy" },
	degraded: { color: "bg-amber-500", label: "Degraded" },
	error: { color: "bg-red-500", label: "Error" },
	offline: { color: "bg-gray-400", label: "Offline" },
	checking: { color: "bg-blue-500", label: "Checking" },
};

export default function StatusDot({
	status = "checking",
	label,
	showLabel = true,
	pulse = false,
	className = "",
}) {
	const normalizedStatus = String(status).toLowerCase();
	const config = STATUS_STYLES[normalizedStatus] ?? STATUS_STYLES.offline;
	const accessibleLabel = label ?? config.label;

	return (
		<span
			role="status"
			aria-live="polite"
			aria-label={accessibleLabel}
			className={`inline-flex items-center gap-2 text-sm text-inherit ${className}`.trim()}
		>
			<span
				aria-hidden="true"
				className={`h-2 w-2 shrink-0 rounded-full ${config.color} ${
					pulse || normalizedStatus === "checking" ? "animate-pulse motion-reduce:animate-none" : ""
				}`}
			/>
			{showLabel && <span>{accessibleLabel}</span>}
		</span>
	);
}
