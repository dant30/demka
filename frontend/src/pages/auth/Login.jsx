import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { landingPathFor } from '@/utils/roles';
import { extractError } from '@/api/client';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await login(identifier, password);
      navigate(landingPathFor(data.user?.role), { replace: true });
    } catch (err) {
      setError(extractError(err, 'Login failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-brand-900 p-4">
      <div className="auth-glass w-full max-w-md rounded-2xl p-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white">DEMKA</h1>
          <p className="text-white/70 text-sm mt-1">Auto Spares & Motorbike Parts</p>
        </div>
        <form onSubmit={handleSubmit} className="auth-fields space-y-4">
          <Input
            label="Username or Phone"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            autoFocus
            required
          />
          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              className="absolute right-2 top-[2.1rem] inline-flex h-9 items-center gap-1 rounded px-2 text-xs font-semibold text-white/80 hover:bg-white/10 hover:text-white"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              title={showPassword ? 'Hide password' : 'Show password'}
            >
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8">
                {showPassword ? (
                  <>
                    <path d="M3 3l18 18M10.6 10.7a2 2 0 002.7 2.7" />
                    <path d="M9.9 5.2A10.8 10.8 0 0112 5c5.2 0 8.5 4.7 9 7-.2 1-1 2.3-2.2 3.5M6.2 6.2C3.9 7.7 2.4 10 2 12c.5 2.3 3.8 7 10 7 1.5 0 2.8-.3 4-.8" />
                  </>
                ) : (
                  <>
                    <path d="M2 12s3.3-7 10-7 10 7 10 7-3.3 7-10 7S2 12 2 12z" />
                    <circle cx="12" cy="12" r="3" />
                  </>
                )}
              </svg>
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
          {error && <div className="rounded-lg border border-red-200/30 bg-red-950/20 px-3 py-2 text-sm text-red-100">{error}</div>}
          <Button type="submit" loading={loading} className="w-full" size="lg">
            Sign in
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-white/70">
          Customer?{' '}
          <Link to="/portal/login" replace className="font-medium text-sky-200 hover:text-white hover:underline">
            Order via portal
          </Link>
        </p>
      </div>
    </div>
  );
}