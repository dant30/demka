import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { portalApi, extractError } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import { usePortal } from '@/store/portal';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function PortalLogin() {
  const navigate = useNavigate();
  const setAuth = usePortal((s) => s.setAuth);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('phone');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const requestOtp = async () => {
    setError('');
    setLoading(true);
    try {
      await portalApi.post(endpoints.preorders.portal.requestOtp, { phone });
      setStep('otp');
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    setError('');
    setLoading(true);
    try {
      const { data } = await portalApi.post(
        endpoints.preorders.portal.verifyOtp, { phone, otp }
      );
      setAuth({ customer: data.customer, token: data.session_token });
      navigate('/portal');
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-brand-900 p-4">
      <div className="auth-glass w-full max-w-md rounded-2xl p-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-white">DEMKA</h1>
          <p className="text-white/70 text-sm mt-1">Reseller Order Portal</p>
        </div>

        {step === 'phone' ? (
          <div className="space-y-4">
            <Input
              label="Phone Number"
              placeholder="07XXXXXXXX"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              autoFocus
            />
            {error && <div className="rounded-lg border border-red-200/30 bg-red-950/20 px-3 py-2 text-sm text-red-100">{error}</div>}
            <Button onClick={requestOtp} loading={loading} className="w-full" size="lg">
              Send OTP
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <Input
              label="OTP Code"
              placeholder="6-digit code from SMS"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              autoFocus
            />
            {error && <div className="rounded-lg border border-red-200/30 bg-red-950/20 px-3 py-2 text-sm text-red-100">{error}</div>}
            <Button onClick={verifyOtp} loading={loading} className="w-full" size="lg">
              Verify & Sign In
            </Button>
            <button
              onClick={() => setStep('phone')}
              className="w-full text-sm text-white/70 hover:text-white hover:underline"
            >
              Use a different number
            </button>
          </div>
        )}
      </div>
    </div>
  );
}