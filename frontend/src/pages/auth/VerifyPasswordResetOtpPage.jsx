import { Key, CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';

import { OtpInput } from '@/components/auth/otp-input';
import { useApiMutation } from '@/hooks/useApiMutation';
import { authApi } from '@/lib/apiClient';

export default function VerifyPasswordResetOtpPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [verified, setVerified] = useState(false);
  const email = location.state?.email || '';

  const { mutate: verifyReset, loading: isVerifying } = useApiMutation(
    (variables) => authApi.verifyPasswordReset(variables),
    {
      onSuccess: () => {
        setVerified(true);
        toast.success('Code verified! Redirecting...');
        setTimeout(() => {
          navigate(`/reset-password?email=${encodeURIComponent(email)}&otp=${otp}`);
        }, 1500);
      },
      onError: (err) => {
        const message = err.response?.data?.error?.message || 'Invalid code. Please try again.';
        setError(message);
      },
    }
  );

  const { mutate: resendCode, loading: isResending } = useApiMutation(
    (variables) => authApi.forgotPassword(variables),
    {
      onSuccess: () => {
        toast.success('New code sent! Check your inbox.');
        setCooldown(30);
        setError('');
      },
      onError: (err) => {
        const message = err.response?.data?.error?.message || 'Could not resend code.';
        setError(message);
      },
    }
  );

  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  const handleSubmit = (e) => {
    e?.preventDefault();

    if (otp.length !== 6) {
      setError('Please enter the complete 6-digit code');
      return;
    }

    if (!email) {
      setError('Email address not found. Please try again.');
      return;
    }

    setError('');
    verifyReset({ email, otp });
  };

  const handleResend = () => {
    if (cooldown > 0) return;

    if (!email) {
      setError('Email address not found. Please try again from the forgot password page.');
      return;
    }

    resendCode({ forgotPasswordRequest: { email } });
  };

  const handleOtpChange = (value) => {
    setOtp(value);
    if (error) setError('');
  };

  const anyLoading = isVerifying || isResending;

  return (
    <main className='relative min-h-screen overflow-hidden font-sans bg-background pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          <div className='flex justify-center mb-6'>
            <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
              {verified ? (
                <CheckCircle className='w-7 h-7 text-green-600' />
              ) : (
                <Key className='w-7 h-7 text-primary' />
              )}
            </div>
          </div>

          <div className='mb-10 text-center'>
            <h1 className='mb-3 font-serif text-5xl font-black tracking-tighter text-primary'>
              {verified ? 'Code Verified!' : 'Enter Reset Code'}
            </h1>
            <p className='text-sm italic font-bold text-primary/40'>
              {verified
                ? 'Redirecting to password reset...'
                : 'Enter the 6-digit code sent to your email'}
            </p>
          </div>

          {verified ? (
            <div className='space-y-6'>
              <div className='p-4 border bg-green-50 border-green-200 rounded-2xl'>
                <p className='text-sm font-bold text-green-800 text-center'>
                  Your code has been verified. You can now create a new password.
                </p>
              </div>
              <Link
                to={`/reset-password?email=${encodeURIComponent(email)}&otp=${otp}`}
                className='block w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all text-center'>
                Continue to Reset Password
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className='space-y-6'>
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1 text-center'>
                  Reset Code
                </label>
                <OtpInput
                  value={otp}
                  onChange={handleOtpChange}
                  disabled={isVerifying}
                  error={!!error}
                />
              </div>

              {error && (
                <div className='flex items-start gap-3 p-4 duration-300 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
                  <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
                  <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
                </div>
              )}

              <button
                type='submit'
                disabled={otp.length !== 6 || anyLoading}
                className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
                {isVerifying ? (
                  <Loader2 className='w-5 h-5 animate-spin' />
                ) : (
                  <>
                    <CheckCircle className='w-5 h-5' />
                    <span>Verify Code</span>
                  </>
                )}
              </button>

              <div className='flex items-center justify-center gap-2 pt-4 border-t border-primary/10'>
                <span className='text-xs font-bold text-primary/40'>Didn't receive the code?</span>
                <button
                  type='button'
                  onClick={handleResend}
                  disabled={cooldown > 0 || isResending}
                  className='text-xs font-black uppercase tracking-[0.2em] text-primary hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline'>
                  {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend'}
                </button>
              </div>
            </form>
          )}

          <div className='mt-20 text-center'>
            <Link
              to='/forgot-password'
              className='text-xs font-bold tracking-widest uppercase transition-opacity opacity-20 hover:opacity-100 inline-flex items-center gap-2'>
              <ArrowLeft className='w-4 h-4' />
              <span>Back to Forgot Password</span>
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
