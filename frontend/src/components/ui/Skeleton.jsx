export function Skeleton({
  className = '',
  rounded = 'rounded-md',
  ...props
}) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block animate-pulse bg-slate-200 ${rounded} ${className}`}
      {...props}
    />
  );
}

export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={index === lines - 1 ? 'h-3 w-2/3' : 'h-3 w-full'}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className = '' }) {
  return (
    <div className={`card space-y-3 ${className}`}>
      <Skeleton className="h-4 w-1/3" />
      <SkeletonText lines={3} />
    </div>
  );
}

export function SkeletonRow({ className = '' }) {
  return (
    <div className={`flex items-center gap-3 py-3 ${className}`}>
      <Skeleton className="h-10 w-10 shrink-0" rounded="rounded-full" />
      <SkeletonText lines={2} className="flex-1" />
    </div>
  );
}

export default Skeleton;
