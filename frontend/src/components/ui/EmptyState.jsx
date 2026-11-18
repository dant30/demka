export default function EmptyState({ icon = '📭', title, description, action, className = '' }) {
  return (
    <div className={`card empty-state text-center py-10 md:py-12 ${className}`} role="status">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="font-semibold text-slate-900 mb-1">{title}</h3>
      {description && <p className="text-slate-600 text-sm mb-4">{description}</p>}
      {action}
    </div>
  );
}