import { ResponseError } from '@bukoo/api-client';
import { CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { authApi } from '@/lib/apiClient';

export default function VerifyPasswordResetPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const email = searchParams.get('email') || '';
  const otp = searchParams.get('otp') || '';

  useEffect(() => {
    async function verifyResetToken() {
      if (!email || !otp) {
        setStatus('error');
        setError('Invalid reset link. Please request a new one.');
        return;
      }

      try {
        await authApi.verifyPasswordReset({ email, otp });
        setStatus('success');
        toast.success('Reset link verified! Redirecting...');
        setTimeout(() => {
          navigate(`/reset-password?email=${encodeURIComponent(email)}&otp=${otp}`);
        }, 2000);
      } catch (err) {
        setStatus('error');
        if (err instanceof ResponseError) {
          const data = await err.response?.json?.();
          setError(data?.error?.message || 'This reset link is invalid or has expired.');
        } else {
          setError('Could not connect to server. Please check your connection.');
        }
      }
    }

    verifyResetToken();
  }, [email, otp, navigate]);

  return (
    <main className='relative min-h-screen overflow-hidden font-sans bg-background pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          {/* Icon Section */}
          <div className='flex justify-center mb-6'>
            <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
              {status === 'loading' && <Loader2 className='w-7 h-7 text-primary animate-spin' />}
              {status === 'success' && <CheckCircle className='w-7 h-7 text-green-600' />}
              {status === 'error' && <AlertCircle className='w-7 h-7 text-destructive' />}
            </div>
          </div>

          {/* Title Section */}
          <div className='mb-10 text-center'>
            <h1 className='mb-3 font-serif text-5xl font-black tracking-tighter text-primary'>
              {status === 'loading' && 'Verifying Reset Link'}
              {status === 'success' && 'Link Verified!'}
              {status === 'error' && 'Invalid Link'}
            </h1>
            <p className='text-sm italic font-bold text-primary/40'>
              {status === 'loading' && 'Please wait while we verify your password reset link'}
              {status === 'success' && 'Redirecting to password reset...'}
              {status === 'error' && error}
            </p>
          </div>

          {/* Loading State */}
          {status === 'loading' && (
            <div className='flex justify-center py-8'>
              <Loader2 className='w-12 h-12 text-primary animate-spin' />
            </div>
          )}

          {/* Success State */}
          {status === 'success' && (
            <div className='space-y-6'>
              <div className='p-4 border bg-green-50 border-green-200 rounded-2xl'>
                <p className='text-sm font-bold text-green-800 text-center'>
                  Reset link verified successfully! You can now create a new password.
                </p>
              </div>
              <Link
                to={`/reset-password?email=${encodeURIComponent(email)}&otp=${otp}`}
                className='block w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all text-center'>
                Continue to Reset Password
              </Link>
            </div>
          )}

          {/* Error State */}
          {status === 'error' && (
            <div className='space-y-6'>
              <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl'>
                <AlertCircle className='w-5 h-5 text-destructive shrink-0 mt-0.5' />
                <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
              </div>
              <Link
                to='/forgot-password'
                className='block w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all text-center'>
                Request New Reset Link
              </Link>
              <div className='text-center'>
                <Link
                  to='/login'
                  className='text-xs font-bold text-primary/60 hover:text-primary hover:underline transition-colors'>
                  Back to Login
                </Link>
              </div>
            </div>
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
