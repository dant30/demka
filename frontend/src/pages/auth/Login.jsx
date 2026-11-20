import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { landingPathFor } from '@/utils/roles';
import { extractError } from '@/api/client';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

function Icon({ name, className = 'h-5 w-5' }) {
  const icons = {
    eye: (
      <>
        <path d="M2 12s3.3-7 10-7 10 7 10 7-3.3 7-10 7S2 12 2 12Z" />
        <circle cx="12" cy="12" r="3" />
      </>
    ),
    eyeOff: (
      <>
        <path d="m3 3 18 18" />
        <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
        <path d="M9.9 5.2A10.8 10.8 0 0 1 12 5c5.2 0 8.5 4.7 9 7-.2 1-1 2.3-2.2 3.5M6.2 6.2C3.9 7.7 2.4 10 2 12c.5 2.3 3.8 7 10 7 1.5 0 2.8-.3 4-.8" />
      </>
    ),
    shield: (
      <>
        <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    package: (
      <>
        <path d="m12 3 9 5-9 5-9-5 9-5Z" />
        <path d="m3 8 9 5 9-5M3 8v10l9 5 9-5V8M12 13v10" />
      </>
    ),
    chart: (
      <>
        <path d="M3 3v18h18" />
        <path d="m19 9-5 5-4-4-5 5" />
      </>
    ),
    arrow: <path d="M5 12h14M12 5l7 7-7 7" />,
    lock: (
      <>
        <rect x="4" y="10" width="16" height="11" rx="2" />
        <path d="M8 10V7a4 4 0 1 1 8 0v3M12 14v3" />
      </>
    ),
    alert: (
      <>
        <path d="M12 9v4M12 17h.01" />
        <path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3l-7.9-14.1a2 2 0 0 0-3.4 0Z" />
      </>
    ),
  };

  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {icons[name]}
    </svg>
  );
}

function BrandLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 text-white shadow-lg shadow-brand-600/20">
        <Icon name="package" className="h-6 w-6" />
      </div>
      <div>
        <h1 className="text-xl font-black tracking-[0.16em] text-white">DEMKA</h1>
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Auto Spares & Motorbike Parts</p>
      </div>
    </div>
  );
}

function Feature({ icon, title, description }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-sky-300">
        <Icon name={icon} className="h-5 w-5" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-white">{title}</h3>
        <p className="mt-1 text-xs leading-5 text-slate-400">{description}</p>
      </div>
    </div>
  );
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (loading) return;

    setError('');
    setLoading(true);

    try {
      const data = await login(identifier.trim(), password);
      navigate(landingPathFor(data.user?.role), { replace: true });
    } catch (err) {
      setError(extractError(err, 'Login failed. Please check your credentials.'));
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => {
    if (error) setError('');
  };

  return (
    <main className="relative flex min-h-screen overflow-hidden bg-slate-950">
      <div aria-hidden="true" className="pointer-events-none absolute -left-40 -top-40 h-96 w-96 rounded-full bg-brand-600/20 blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-sky-600/10 blur-3xl" />

      <aside className="relative hidden w-[48%] flex-col justify-between overflow-hidden border-r border-white/10 bg-gradient-to-br from-slate-900 via-slate-900 to-brand-900 p-10 xl:flex">
        <BrandLogo />

        <div className="relative z-10 max-w-xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-500/10 px-3 py-1.5 text-xs font-semibold text-sky-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Business management platform
          </div>

          <h2 className="text-4xl font-bold leading-tight tracking-tight text-white 2xl:text-5xl">
            Keep your business moving.
            <span className="mt-2 block bg-gradient-to-r from-sky-300 to-sky-100 bg-clip-text text-transparent">
              Manage smarter with DEMKA.
            </span>
          </h2>

          <p className="mt-6 max-w-md text-base leading-7 text-slate-400">
            Your central workspace for managing auto spares, motorbike parts, inventory, sales and daily business operations.
          </p>

          <div className="mt-10 grid gap-6">
            <Feature icon="package" title="Inventory management" description="Keep track of products, quantities, pricing and stock movement." />
            <Feature icon="chart" title="Sales visibility" description="Manage transactions and get a clearer picture of business performance." />
            <Feature icon="shield" title="Controlled access" description="Role-based access keeps business operations organized." />
          </div>
        </div>

        <p className="relative z-10 text-xs text-slate-500">DEMKA Business Management System</p>

        <div aria-hidden="true" className="pointer-events-none absolute -bottom-28 -right-24 h-96 w-96 rounded-full border border-white/5">
          <div className="absolute inset-10 rounded-full border border-white/5" />
          <div className="absolute inset-20 rounded-full border border-white/5" />
        </div>
      </aside>

      <section className="relative z-10 flex min-h-screen w-full flex-col items-center justify-center px-4 py-8 sm:px-8 xl:w-[52%]">
        <div className="w-full max-w-md">
          <div className="mb-8 xl:hidden">
            <BrandLogo />
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Welcome back</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Sign in to access your DEMKA business workspace.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              className="[&_.label]:text-slate-300 [&_.input]:border-slate-700 [&_.input]:bg-slate-900/80 [&_.input]:text-white [&_.input]:placeholder-slate-500 [&_.input]:focus:bg-slate-900 [&_.input]:focus:border-sky-500 [&_.input]:focus:ring-sky-500 [&_.input:disabled]:bg-slate-900 [&_.input:disabled]:text-slate-500"
              label="Username or Phone"
              value={identifier}
              onChange={(event) => {
                setIdentifier(event.target.value);
                clearError();
              }}
              autoFocus
              autoComplete="username"
              placeholder="Enter your username or phone"
              required
              disabled={loading}
            />

            <div className="relative">
              <Input
                className="[&_.label]:text-slate-300 [&_.input]:border-slate-700 [&_.input]:bg-slate-900/80 [&_.input]:pr-20 [&_.input]:text-white [&_.input]:placeholder-slate-500 [&_.input]:focus:bg-slate-900 [&_.input]:focus:border-sky-500 [&_.input]:focus:ring-sky-500 [&_.input:disabled]:bg-slate-900 [&_.input:disabled]:text-slate-500"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  clearError();
                }}
                autoComplete="current-password"
                placeholder="Enter your password"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                className="absolute right-2 top-[2.1rem] inline-flex h-9 items-center gap-1.5 rounded-lg px-2 text-xs font-semibold text-slate-400 transition hover:bg-slate-700/50 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
              >
                <Icon name={showPassword ? 'eyeOff' : 'eye'} className="h-4 w-4" />
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>

            {error && (
              <div role="alert" aria-live="assertive" className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                <Icon name="alert" className="mt-0.5 h-5 w-5 shrink-0" />
                <p className="leading-5">{error}</p>
              </div>
            )}

            <div className="flex justify-end">
              <Link to="/password-reset" className="text-sm font-semibold text-sky-300 transition hover:text-sky-200 hover:underline">
                Forgot password?
              </Link>
            </div>

            <Button
              type="submit"
              loading={loading}
              loadingText="Signing in..."
              disabled={loading || !identifier.trim() || !password}
              className="w-full"
              size="lg"
            >
              Sign in
            </Button>
          </form>

          <div className="mt-8 rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white">Shopping with DEMKA?</p>
                <p className="mt-1 text-xs text-slate-400">Access your customer ordering portal.</p>
              </div>
              <Link to="/portal/login" className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-sky-400/40 hover:bg-sky-500/10 hover:text-white">
                Customer portal
                <Icon name="arrow" className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          <div className="mt-10 border-t border-white/10 pt-5 text-center">
            <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
              <Icon name="shield" className="h-4 w-4" />
              Secure business account access
            </div>
            <p className="mt-3 text-[11px] text-slate-600">© {new Date().getFullYear()} DEMKA. All rights reserved.</p>
          </div>
        </div>
      </section>
    </main>
  );
}