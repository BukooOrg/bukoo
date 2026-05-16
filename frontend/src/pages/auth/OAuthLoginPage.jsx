import { ResponseError } from '@bukoo/api-client';
import { AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';

import { authApi } from '@/lib/apiClient';

function GoogleIcon() {
  return (
    <svg viewBox='0 0 24 24' className='w-14 h-14' xmlns='http://www.w3.org/2000/svg'>
      <path
        d='M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z'
        fill='#4285F4'
      />
      <path
        d='M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z'
        fill='#34A853'
      />
      <path
        d='M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z'
        fill='#FBBC05'
      />
      <path
        d='M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z'
        fill='#EA4335'
      />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg viewBox='0 0 24 24' className='w-14 h-14' xmlns='http://www.w3.org/2000/svg'>
      <path
        d='M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z'
        fill='#1877F2'
      />
    </svg>
  );
}

const providerIcons = {
  google: GoogleIcon,
  facebook: FacebookIcon,
};

export default function OAuthLoginPage() {
  const { provider } = useParams();
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');

  const ProviderIcon = providerIcons[provider?.toLowerCase()] || null;

  useEffect(() => {
    async function getOAuthUrl() {
      if (!provider) {
        setStatus('error');
        setError('Invalid sign-in link. Please try again.');
        return;
      }

      try {
        const response = await authApi.getOAuthLoginUrl({ provider });
        if (response.data?.url) {
          window.location.href = response.data.url;
        } else {
          setStatus('error');
          setError('Could not start sign-in. Please try again.');
        }
      } catch (err) {
        setStatus('error');
        if (err instanceof ResponseError) {
          const data = await err.response?.json?.();
          setError(data?.error?.message || 'Could not start sign-in. Please try again.');
        } else {
          setError('Could not connect to server. Please check your connection.');
        }
      }
    }

    getOAuthUrl();
  }, [provider]);

  return (
    <main className='relative min-h-screen overflow-hidden font-sans bg-background pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          {/* Icon Section */}
          <div className='flex justify-center mb-6'>
            <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
              {status === 'loading' && ProviderIcon && <ProviderIcon />}
              {status === 'loading' && !ProviderIcon && (
                <Loader2 className='w-7 h-7 text-primary animate-spin' />
              )}
              {status === 'error' && <AlertCircle className='w-7 h-7 text-destructive' />}
            </div>
          </div>

          {/* Title Section */}
          <div className='mb-10 text-center'>
            <h1 className='mb-3 font-serif text-5xl font-black tracking-tighter text-primary'>
              {status === 'loading' &&
                `Connecting to ${provider?.charAt(0).toUpperCase() + provider?.slice(1)}`}
              {status === 'error' && 'Sign-In Failed'}
            </h1>
            <p className='text-sm italic font-bold text-primary/40'>
              {status === 'loading' && 'Please wait while we redirect you...'}
              {status === 'error' && error}
            </p>
          </div>

          {/* Loading State */}
          {status === 'loading' && (
            <div className='flex justify-center py-8'>
              <Loader2 className='w-12 h-12 text-primary animate-spin' />
            </div>
          )}

          {/* Error State */}
          {status === 'error' && (
            <div className='space-y-6'>
              <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl'>
                <AlertCircle className='w-5 h-5 text-destructive shrink-0 mt-0.5' />
                <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
              </div>
              <button
                onClick={() => window.location.reload()}
                className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all'>
                Try Again
              </button>
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
