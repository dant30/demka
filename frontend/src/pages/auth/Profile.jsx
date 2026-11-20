import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import PageHeader from '@/components/ui/PageHeader';
import StatusDot from '@/components/ui/StatusDot';
import { useAuth } from '@/hooks/useAuth';

function displayDate(value) {
  if (!value) return 'Not available';

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? 'Not available'
    : new Intl.DateTimeFormat('en-KE', {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(date);
}

function roleLabel(role) {
  if (!role) return 'Not available';

  return role
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function getInitials(name) {
  return (
    name
      ?.trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part.charAt(0))
      .join('')
      .toUpperCase() || '?'
  );
}

function Icon({ name, className = 'h-5 w-5' }) {
  const common = {
    className,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.7,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    viewBox: '0 0 24 24',
    'aria-hidden': true,
  };

  const paths = {
    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M5 21a7 7 0 0 1 14 0" />
      </>
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="4" width="18" height="17" rx="2" />
        <path d="M16 2v4M8 2v4M3 10h18" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    mail: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m3 7 9 6 9-6" />
      </>
    ),
    phone: (
      <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.4 19.4 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2Z" />
    ),
    at: (
      <>
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="3.5" />
        <path d="M15.5 12v2a2 2 0 0 0 4 0v-2" />
      </>
    ),
    badge: (
      <>
        <circle cx="12" cy="8" r="6" />
        <path d="m8.5 13-1 9 4.5-2.5 4.5 2.5-1-9" />
      </>
    ),
  };

  return <svg {...common}>{paths[name] || paths.user}</svg>;
}

function ProfileField({ label, value, icon }) {
  return (
    <div className="flex min-w-0 items-start gap-3 border-b border-slate-100 py-4 last:border-b-0 dark:border-slate-800">
      {icon && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          <Icon name={icon} className="h-4 w-4" />
        </div>
      )}

      <div className="min-w-0 flex-1">
        <dt className="text-xs font-medium text-slate-500 dark:text-slate-400">
          {label}
        </dt>
        <dd className="mt-1 break-words text-sm font-semibold text-slate-900 dark:text-slate-100">
          {value || 'Not provided'}
        </dd>
      </div>
    </div>
  );
}

function SectionCard({ title, description, icon, children }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-4 sm:px-5 dark:border-slate-800">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-400">
          <Icon name={icon} />
        </div>

        <div className="min-w-0">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white sm:text-base">
            {title}
          </h2>
          {description && (
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              {description}
            </p>
          )}
        </div>
      </div>

      <dl className="grid grid-cols-1 gap-x-0 px-4 sm:grid-cols-2 sm:gap-x-8 sm:px-5">
        {children}
      </dl>
    </section>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-5 animate-pulse">
      <div className="h-40 rounded-2xl bg-slate-200 dark:bg-slate-800" />

      {[1, 2].map((item) => (
        <div
          key={item}
          className="rounded-2xl border border-slate-200 p-5 dark:border-slate-800"
        >
          <div className="h-5 w-40 rounded bg-slate-200 dark:bg-slate-800" />
          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            {[1, 2, 3, 4].map((field) => (
              <div key={field}>
                <div className="h-3 w-20 rounded bg-slate-200 dark:bg-slate-800" />
                <div className="mt-2 h-4 w-36 rounded bg-slate-200 dark:bg-slate-800" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Profile() {
  const { user: cachedUser } = useAuth();

  const {
    data: fetchedUser,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['my-profile'],
    queryFn: async () => (await api.get(endpoints.auth.me)).data,
    staleTime: 60_000,
    retry: 1,
  });

  const user = fetchedUser ?? cachedUser;

  const fullName =
    user?.full_name ||
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') ||
    user?.username ||
    'User';

  const initials = getInitials(fullName);

  const accountStatus =
    user?.is_active === undefined
      ? isLoading
        ? 'Checking account status'
        : 'Status unavailable'
      : user.is_active
        ? 'Active account'
        : 'Inactive account';

  const statusDot =
    user?.is_active === undefined
      ? isLoading
        ? 'checking'
        : 'offline'
      : user.is_active
        ? 'healthy'
        : 'error';

  if (isLoading && !cachedUser) {
    return (
      <div className="mx-auto max-w-5xl space-y-5">
        <PageHeader
          title="My Profile"
          description="Your account details and access information."
        />
        <ProfileSkeleton />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-5 pb-6">
      <PageHeader
        title="My Profile"
        description="Manage and review your account information."
      />

      {isError && (
        <div
          role="status"
          className="flex flex-col gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-amber-900/50 dark:bg-amber-950/20"
        >
          <p className="text-sm text-amber-800 dark:text-amber-300">
            Some profile details could not be refreshed. Showing available account information.
          </p>

          <button
            type="button"
            onClick={() => refetch()}
            className="shrink-0 self-start text-xs font-bold text-amber-800 underline underline-offset-4 hover:text-amber-950 dark:text-amber-300"
          >
            Try again
          </button>
        </div>
      )}

      <section className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-r from-brand-700 via-brand-600 to-brand-500 sm:h-28" />

        <div className="relative px-4 pb-5 pt-10 sm:px-6 sm:pt-14">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div
              aria-label={accountStatus}
              className="relative flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl border-4 border-white bg-slate-100 text-2xl font-bold text-brand-700 shadow-md dark:border-slate-900 dark:bg-slate-800 dark:text-brand-400 sm:h-24 sm:w-24 sm:text-3xl"
            >
              {initials}
              <StatusDot
                status={statusDot}
                label={accountStatus}
                showLabel={false}
                className="absolute -bottom-1 -right-1"
              />
            </div>

            <div className="min-w-0 flex-1 sm:pb-1">
              <h2 className="break-words text-xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-2xl">
                {fullName}
              </h2>

              <p className="mt-1 break-all text-sm text-slate-500 dark:text-slate-400">
                @{user?.username || '—'}
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-500/10 dark:text-brand-400">
                  <Icon name="badge" className="h-3.5 w-3.5" />
                  {roleLabel(user?.role)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <SectionCard
          title="Personal information"
          description="Your basic contact details"
          icon="user"
        >
          <ProfileField
            label="First name"
            value={user?.first_name}
            icon="user"
          />
          <ProfileField
            label="Last name"
            value={user?.last_name}
            icon="user"
          />
          <ProfileField
            label="Email address"
            value={user?.email}
            icon="mail"
          />
          <ProfileField
            label="Phone number"
            value={user?.phone}
            icon="phone"
          />
        </SectionCard>

        <SectionCard
          title="Account information"
          description="Your account and access details"
          icon="shield"
        >
          <ProfileField
            label="Username"
            value={user?.username}
            icon="at"
          />
          <ProfileField
            label="Account role"
            value={roleLabel(user?.role)}
            icon="badge"
          />
          <ProfileField
            label="Member since"
            value={displayDate(user?.created_at)}
            icon="calendar"
          />
          <ProfileField
            label="Last login"
            value={displayDate(user?.last_login)}
            icon="clock"
          />
        </SectionCard>
      </div>

      <div className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/60">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
          <Icon name="shield" />
        </div>

        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
            Account information
          </h3>
          <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
            Your profile information is associated with your account. Contact your administrator if any of these details need to be corrected.
          </p>
        </div>
      </div>
    </div>
  );
}

