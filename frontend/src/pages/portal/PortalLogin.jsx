import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { portalApi, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { usePortal } from '@/store/portal';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

function AlertIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0" aria-hidden="true">
      <path d="M12 9v4M12 17h.01" />
      <path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3l-7.9-14.1a2 2 0 0 0-3.4 0Z" />
    </svg>
  );
}

export default function PortalLogin() {
  const navigate = useNavigate();
  const setAuth = usePortal((state) => state.setAuth);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('phone');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const requestOtp = async (event) => {
    event.preventDefault();
    if (loading) return;

    setError('');
    setLoading(true);
    try {
      await portalApi.post(endpoints.preorders.portal.requestOtp, { phone: phone.trim() });
      setStep('otp');
    } catch (err) {
      setError(extractError(err, 'We could not send the verification code.'));
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async (event) => {
    event.preventDefault();
    if (loading) return;

    setError('');
    setLoading(true);
    try {
      const { data } = await portalApi.post(
        endpoints.preorders.portal.verifyOtp,
        { phone: phone.trim(), otp: otp.trim() }
      );
      setAuth({ customer: data.customer, token: data.session_token });
      navigate('/portal', { replace: true });
    } catch (err) {
      setError(extractError(err, 'The verification code could not be verified.'));
    } finally {
      setLoading(false);
    }
  };

  const goBackToPhone = () => {
    setOtp('');
    setError('');
    setStep('phone');
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-4 py-8 sm:px-6">
      <div aria-hidden="true" className="pointer-events-none absolute -left-32 -top-32 h-80 w-80 rounded-full bg-brand-600/20 blur-3xl" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-36 -right-32 h-80 w-80 rounded-full bg-sky-600/10 blur-3xl" />

      <div className="relative z-10 w-full max-w-md">
        <div className="mb-7 flex items-center justify-center gap-3 sm:justify-start">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 text-white shadow-lg shadow-brand-600/20">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6" aria-hidden="true">
              <path d="m12 3 9 5-9 5-9-5 9-5Z" />
              <path d="m3 8 9 5 9-5M3 8v10l9 5 9-5V8M12 13v10" />
            </svg>
          </div>
          <div>
            <p className="text-xl font-black tracking-[0.16em] text-white">DEMKA</p>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Customer portal</p>
          </div>
        </div>

        <section className="rounded-2xl border border-white/10 bg-slate-900/80 p-5 shadow-2xl shadow-black/20 backdrop-blur sm:p-8" aria-labelledby="portal-login-heading">
          <div className="mb-7">
            <div className="mb-5 flex items-center gap-2" aria-label={step === 'phone' ? 'Step 1 of 2' : 'Step 2 of 2'}>
              <span className="h-1.5 w-8 rounded-full bg-brand-500" />
              <span className={`h-1.5 w-8 rounded-full ${step === 'otp' ? 'bg-brand-500' : 'bg-slate-700'}`} />
              <span className="ml-1 text-xs font-semibold text-slate-500">{step === 'phone' ? '1 of 2' : '2 of 2'}</span>
            </div>

            <h1 id="portal-login-heading" className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
              {step === 'phone' ? 'Welcome to your portal' : 'Enter your verification code'}
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {step === 'phone'
                ? 'Enter the phone number linked to your DEMKA account.'
                : `We sent a 6-digit code to ${phone.trim()}.`}
            </p>
          </div>

          {step === 'phone' ? (
            <form onSubmit={requestOtp} className="space-y-5">
              <Input
                className="[&_.label]:text-slate-300 [&_.input]:border-slate-700 [&_.input]:bg-slate-950/70 [&_.input]:text-white [&_.input]:placeholder-slate-500 [&_.input]:focus:bg-slate-950 [&_.input]:focus:border-sky-500 [&_.input]:focus:ring-sky-500 [&_.input:disabled]:bg-slate-950 [&_.input:disabled]:text-slate-500"
                label="Phone number"
                placeholder="07XXXXXXXX"
                value={phone}
                onChange={(event) => {
                  setPhone(event.target.value);
                  if (error) setError('');
                }}
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                autoFocus
                required
                disabled={loading}
              />

              {error && (
                <div role="alert" aria-live="assertive" className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  <AlertIcon />
                  <p className="leading-5">{error}</p>
                </div>
              )}

              <Button
                type="submit"
                loading={loading}
                loadingText="Sending code..."
                disabled={loading || !phone.trim()}
                className="w-full"
                size="lg"
              >
                Send verification code
              </Button>
            </form>
          ) : (
            <form onSubmit={verifyOtp} className="space-y-5">
              <Input
                className="[&_.label]:text-slate-300 [&_.input]:border-slate-700 [&_.input]:bg-slate-950/70 [&_.input]:text-center [&_.input]:text-lg [&_.input]:font-bold [&_.input]:tracking-[0.35em] [&_.input]:text-white [&_.input]:placeholder-slate-600 [&_.input]:placeholder:tracking-normal [&_.input]:placeholder:font-normal [&_.input]:focus:bg-slate-950 [&_.input]:focus:border-sky-500 [&_.input]:focus:ring-sky-500 [&_.input:disabled]:bg-slate-950 [&_.input:disabled]:text-slate-500"
                label="Verification code"
                placeholder="6-digit code"
                value={otp}
                onChange={(event) => {
                  setOtp(event.target.value.replace(/\D/g, '').slice(0, 6));
                  if (error) setError('');
                }}
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                autoFocus
                required
                disabled={loading}
              />

              {error && (
                <div role="alert" aria-live="assertive" className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  <AlertIcon />
                  <p className="leading-5">{error}</p>
                </div>
              )}

              <Button
                type="submit"
                loading={loading}
                loadingText="Verifying..."
                disabled={loading || otp.trim().length !== 6}
                className="w-full"
                size="lg"
              >
                Verify & sign in
              </Button>

              <button
                type="button"
                onClick={goBackToPhone}
                disabled={loading}
                className="w-full text-sm font-semibold text-slate-400 transition hover:text-white hover:underline disabled:cursor-not-allowed disabled:opacity-50"
              >
                Use a different number
              </button>
            </form>
          )}
        </section>

        <Link
          to="/login"
          className="mt-6 flex items-center justify-center gap-2 text-sm font-semibold text-slate-400 transition hover:text-white"
        >
          Staff sign in
          <ArrowIcon />
        </Link>
      </div>
    </main>
  );
}