import { ResponseError } from '@bukoo/api-client';
import { Key, Mail, Send, CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { useApiMutation } from '@/hooks/useApiMutation';
import { authApi } from '@/lib/apiClient';

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get('email') || '');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  // Cooldown timer for resend
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  const { mutate: forgotPassword, loading: isApiSubmitting } = useApiMutation(
    (variables) => authApi.forgotPassword(variables),
    {
      onSuccess: () => {
        setSuccess(true);
        toast.success('Password reset email sent! Check your inbox.');
        setCooldown(30);
        setError('');
        setTimeout(() => {
          navigate('/verify-password-reset-otp', { state: { email: email.trim() } });
        }, 2000);
      },
      onError: (err) => {
        if (err instanceof ResponseError) {
          err.response?.json?.().then((data) => {
            setError(data?.error?.message || 'Failed to send reset email');
          });
        } else {
          setError('Something went wrong. Please try again later.');
        }
      },
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();

    // Client-side validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !emailRegex.test(email.trim())) {
      setError('Please enter a valid email address');
      return;
    }

    setError('');
    forgotPassword({ forgotPasswordRequest: { email: email.trim() } });
  };

  const handleResend = () => {
    if (cooldown > 0) return;

    setError('');
    forgotPassword({ forgotPasswordRequest: { email: email.trim() } });
  };

  return (
    <main className='relative min-h-screen overflow-hidden font-sans bg-background pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          {/* Icon Section */}
          <div className='flex justify-center mb-6'>
            <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
              {success ? (
                <CheckCircle className='w-7 h-7 text-green-600' />
              ) : (
                <Key className='w-7 h-7 text-primary' />
              )}
            </div>
          </div>

          {/* Title Section */}
          <div className='mb-10 text-center'>
            <h1 className='mb-3 font-serif text-5xl font-black tracking-tighter text-primary'>
              {success ? 'Email Sent!' : 'Forgot Password?'}
            </h1>
            <p className='text-sm italic font-bold text-primary/40'>
              {success
                ? "We've sent reset instructions to your email"
                : 'Enter your email and we will send you reset instructions'}
            </p>
          </div>

          {/* Success State */}
          {success ? (
            <div className='space-y-6'>
              <div className='p-4 border bg-green-50 border-green-200 rounded-2xl'>
                <p className='text-sm font-bold text-green-800 text-center'>
                  Check your inbox! We've sent password reset instructions to{' '}
                  <span className='font-black'>{email}</span>
                </p>
                <p className='text-xs text-green-600 text-center mt-2'>
                  Didn't receive the email? Check your spam folder or click 'Resend' below.
                </p>
              </div>

              {/* Resend Section */}
              <div className='flex items-center justify-center gap-2 pt-4 border-t border-primary/10'>
                <span className='text-xs font-bold text-primary/40'>Didn't receive the email?</span>
                <button
                  type='button'
                  onClick={handleResend}
                  disabled={cooldown > 0 || isApiSubmitting}
                  className='text-xs font-black uppercase tracking-[0.2em] text-primary hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline'>
                  {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend'}
                </button>
              </div>

              {/* Back to Login */}
              <Link
                to='/login'
                className='block w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all text-center'>
                Go to Login
              </Link>
            </div>
          ) : (
            /* Email Form */
            <form onSubmit={handleSubmit} className='space-y-6'>
              {/* Email Input */}
              <div className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  Email Address
                </label>
                <div className='relative group'>
                  <div className='absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none'>
                    <Mail className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                  </div>
                  <input
                    type='email'
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (error) setError('');
                    }}
                    required
                    placeholder='Enter your email address'
                    disabled={isApiSubmitting}
                    className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold disabled:opacity-50 disabled:cursor-not-allowed'
                  />
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className='flex items-start gap-3 p-4 duration-300 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
                  <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
                  <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
                </div>
              )}

              {/* Submit Button */}
              <button
                type='submit'
                disabled={!email.trim() || isApiSubmitting}
                className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
                {isApiSubmitting ? (
                  <Loader2 className='w-5 h-5 animate-spin' />
                ) : (
                  <>
                    <Send className='w-5 h-5' />
                    <span>Send Reset Instructions</span>
                  </>
                )}
              </button>

              {/* Back to Login Link */}
              <div className='text-center pt-4'>
                <Link
                  to='/login'
                  className='text-xs font-bold text-primary/60 hover:text-primary hover:underline transition-colors'>
                  Remember your password? <span className='font-black'>Login</span>
                </Link>
              </div>
            </form>
          )}

          {/* Back to Home */}
          <div className='mt-20 text-center'>
            <Link
              to='/'
              className='text-xs font-bold tracking-widest uppercase transition-opacity opacity-20 hover:opacity-100 inline-flex items-center gap-2'>
              <ArrowLeft className='w-4 h-4' />
              <span>Back to Home</span>
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
