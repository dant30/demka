import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function PasswordReset() {
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const requestCode = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const { data } = await api.post(endpoints.auth.passwordResetRequest, { phone });
      setMessage(data.detail || 'If the phone is registered, an OTP has been sent.');
      setCodeSent(true);
    } catch (requestError) {
      setError(extractError(requestError, 'Could not request a reset code.'));
    } finally {
      setLoading(false);
    }
  };

  const confirmReset = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const { data } = await api.post(endpoints.auth.passwordResetConfirm, {
        phone,
        otp,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setMessage(data.detail || 'Password reset successful.');
      setCodeSent(false);
      setOtp('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (requestError) {
      setError(extractError(requestError, 'Could not reset the password.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 to-brand-900 p-4">
      <div className="mx-auto flex min-h-[calc(100dvh-2rem)] w-full max-w-md items-center">
        <section className="auth-glass w-full rounded-2xl p-5 sm:p-8">
          <header className="mb-6 text-center">
            <h1 className="text-2xl font-bold text-white">Reset password</h1>
            <p className="mt-2 text-sm text-white/70">
              {codeSent ? 'Enter the code and choose a new password.' : 'Request a one-time code for your staff account.'}
            </p>
          </header>

          {!codeSent ? (
            <form onSubmit={requestCode} className="space-y-4">
              <Input
                label="Phone number"
                type="tel"
                autoComplete="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                required
              />
              <Button type="submit" loading={loading} className="w-full" size="lg">
                Send reset code
              </Button>
            </form>
          ) : (
            <form onSubmit={confirmReset} className="space-y-4">
              <Input
                label="Phone number"
                type="tel"
                autoComplete="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                required
              />
              <Input
                label="One-time code"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={otp}
                onChange={(event) => setOtp(event.target.value)}
                required
              />
              <Input
                label="New password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                required
              />
              <Input
                label="Confirm new password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
              />
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <Button type="submit" loading={loading} className="w-full" size="lg">
                  Update password
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  className="w-full"
                  onClick={() => { setCodeSent(false); setError(''); setMessage(''); }}
                  disabled={loading}
                >
                  Request another code
                </Button>
              </div>
            </form>
          )}

          {message && <p role="status" className="mt-4 rounded-md bg-emerald-950/20 px-3 py-2 text-sm text-emerald-100">{message}</p>}
          {error && <p role="alert" className="mt-4 rounded-md bg-red-950/20 px-3 py-2 text-sm text-red-100">{error}</p>}
          <p className="mt-6 text-center text-sm text-white/70">
            <Link to="/login" className="font-medium text-sky-200 hover:text-white hover:underline">Back to sign in</Link>
          </p>
        </section>
      </div>
    </main>
  );
}