import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';
import { setToken, userApi } from '@/lib/apiClient';

const ERROR_MESSAGES = {
  OAUTH_STATE_INVALID: 'Your login session expired or was invalid. Please try again.',
  OAUTH_PROVIDER_NOT_FOUND: 'The authentication provider was not found.',
  GOOGLE_OAUTH_ERROR: 'Google sign-in failed. Please try again.',
  FACEBOOK_OAUTH_ERROR: 'Facebook sign-in failed. Please try again.',
  USER_SUSPENDED: 'Your account has been suspended. Please contact support.',
};

export default function OAuthCallbackPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState('loading');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const errorCode = searchParams.get('error');

    if (errorCode) {
      setErrorMsg(ERROR_MESSAGES[errorCode] ?? 'Authentication failed. Please try again.');
      setStatus('error');
      return;
    }

    const hashParams = new URLSearchParams(window.location.hash.slice(1));
    const token = hashParams.get('token');

    if (!token) {
      setErrorMsg('Authentication token missing. Please try again.');
      setStatus('error');
      return;
    }

    setToken(token);

    async function completeOAuth() {
      try {
        const userData = await userApi.getMe();
        login(userData.data);
        setStatus('success');
        setTimeout(
          () => navigate(userData.data?.role === 'admin' ? '/admin' : '/', { replace: true }),
          1500
        );
      } catch {
        setErrorMsg('Failed to complete sign-in. Please try again.');
        setStatus('error');
      }
    }

    completeOAuth();
  }, []);

  return (
    <main className='relative min-h-screen overflow-hidden font-sans bg-background'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative z-10 flex flex-col items-center justify-center min-h-screen p-6'>
        <div className='max-w-sm w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl text-center animate-in fade-in zoom-in duration-700'>
          {status === 'loading' && (
            <>
              <div className='flex justify-center mb-6'>
                <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
                  <Loader2 className='w-7 h-7 text-primary animate-spin' />
                </div>
              </div>
              <h1 className='mb-2 font-serif text-3xl font-black tracking-tighter text-primary'>
                Signing you in
              </h1>
              <p className='text-sm italic font-bold text-primary/40'>Please wait a moment…</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className='flex justify-center mb-6'>
                <div className='flex items-center justify-center rounded-full w-14 h-14 bg-green-50'>
                  <CheckCircle2 className='text-green-600 w-7 h-7' />
                </div>
              </div>
              <h1 className='mb-2 font-serif text-3xl font-black tracking-tighter text-primary'>
                You&apos;re in!
              </h1>
              <p className='text-sm italic font-bold text-primary/40'>
                Redirecting to your bookshelf…
              </p>
            </>
          )}

          {status === 'error' && (
            <>
              <div className='flex justify-center mb-6'>
                <div className='flex items-center justify-center rounded-full w-14 h-14 bg-destructive/5'>
                  <AlertCircle className='w-7 h-7 text-destructive' />
                </div>
              </div>
              <h1 className='mb-3 font-serif text-3xl font-black tracking-tighter text-primary'>
                Sign-in failed
              </h1>
              <p className='mb-8 text-sm font-bold leading-relaxed text-primary/50'>{errorMsg}</p>
              <Link
                to='/login'
                className='inline-block w-full py-4 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] text-xs shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all'>
                Back to Login
              </Link>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
