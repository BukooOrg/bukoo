import { ResponseError } from '@bukoo/api-client';
import { User, Lock, LogIn, AlertCircle, Loader2 } from 'lucide-react';
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';
import { authApi } from '@/lib/apiClient';

function GoogleIcon() {
  return (
    <svg viewBox='0 0 24 24' className='w-5 h-5 shrink-0' xmlns='http://www.w3.org/2000/svg'>
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
    <svg viewBox='0 0 24 24' className='w-5 h-5 shrink-0' xmlns='http://www.w3.org/2000/svg'>
      <path
        d='M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z'
        fill='#1877F2'
      />
    </svg>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const email = formData.get('email');
    const password = formData.get('password');

    try {
      const res = await authApi.credentialLogin({
        loginRequest: {
          email,
          password,
        },
      });

      if (login) {
        login(res.data);
      }

      navigate('/');
    } catch (err) {
      console.error(err);
      if (err instanceof ResponseError) {
        setError('Invalid email or password');
      } else {
        setError('Something went wrong. Please try again later.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthLogin = async (provider) => {
    setOauthLoading(provider);
    setError('');
    try {
      const res = await authApi.getOAuthLoginUrl({ provider });
      window.location.href = res.data.url;
    } catch {
      setError('Could not start sign-in. Please try again.');
      setOauthLoading(null);
    }
  };

  const anyLoading = isLoading || oauthLoading !== null;

  return (
    <main className='relative min-h-screen overflow-hidden font-sans bg-background pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          <div className='mb-10 text-center'>
            <div className='flex justify-center mb-6'>
              <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
                <LogIn className='w-7 h-7 text-primary' />
              </div>
            </div>
            <h1 className='mb-3 font-serif text-5xl font-black tracking-tighter text-primary'>
              Welcome
            </h1>
            <p className='text-sm italic font-bold text-primary/40'>Access your Bukoo account</p>
          </div>

          <form onSubmit={handleSubmit} className='space-y-6'>
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Email Address
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none'>
                  <User className='w-5 h-5 transition-colors text-primary/30 group-focus-within:text-primary' />
                </div>
                <input
                  type='email'
                  name='email'
                  required
                  placeholder='Enter your email'
                  className='w-full py-4 pl-12 pr-4 font-sans font-bold transition-all border md:py-5 bg-white/40 border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
                />
              </div>
            </div>

            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Password
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none'>
                  <Lock className='w-5 h-5 transition-colors text-primary/30 group-focus-within:text-primary' />
                </div>
                <input
                  type='password'
                  name='password'
                  required
                  placeholder='Enter your password'
                  className='w-full py-4 pl-12 pr-4 font-sans font-medium transition-all border bg-white/40 border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
                />
              </div>
            </div>

            <div className='flex items-center justify-between px-1'>
              <label className='flex items-center gap-3 cursor-pointer group'>
                <input
                  type='checkbox'
                  className='w-5 h-5 rounded-lg border-primary/10 text-primary focus:ring-primary/20'
                />
                <span className='text-xs font-bold transition-colors text-primary/40 group-hover:text-primary'>
                  Remember me
                </span>
              </label>
              <Link to='#' className='text-xs font-black text-primary hover:underline'>
                Forgot Password?
              </Link>
            </div>

            {error && (
              <div className='flex items-start gap-3 p-4 duration-300 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
                <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
                <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
              </div>
            )}

            <button
              type='submit'
              disabled={anyLoading}
              className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50'>
              {isLoading ? (
                <Loader2 className='w-5 h-5 animate-spin' />
              ) : (
                <>
                  <LogIn className='w-5 h-5' />
                  <span>Login Account Now</span>
                </>
              )}
            </button>
          </form>

          <div className='flex items-center gap-4 my-6'>
            <div className='flex-1 h-px bg-primary/10' />
            <span className='text-[11px] font-black uppercase tracking-[0.2em] text-primary/30'>
              or
            </span>
            <div className='flex-1 h-px bg-primary/10' />
          </div>

          <div className='flex flex-col gap-3'>
            <button
              type='button'
              onClick={() => handleOAuthLogin('google')}
              disabled={anyLoading}
              className='w-full py-4 bg-white/40 border border-primary/10 rounded-2xl font-sans font-bold text-sm text-primary hover:bg-white/70 hover:border-primary/20 active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50'>
              {oauthLoading === 'google' ? (
                <Loader2 className='w-5 h-5 animate-spin' />
              ) : (
                <GoogleIcon />
              )}
              <span>Continue with Google</span>
            </button>

            <button
              type='button'
              onClick={() => handleOAuthLogin('facebook')}
              disabled={anyLoading}
              className='w-full py-4 bg-white/40 border border-primary/10 rounded-2xl font-sans font-bold text-sm text-primary hover:bg-white/70 hover:border-primary/20 active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50'>
              {oauthLoading === 'facebook' ? (
                <Loader2 className='w-5 h-5 animate-spin' />
              ) : (
                <FacebookIcon />
              )}
              <span>Continue with Facebook</span>
            </button>
          </div>

          <p className='mt-10 text-xs font-bold text-center text-primary/40'>
            Don&apos;t have an account?{' '}
            <Link
              to='/register'
              className='ml-1 font-black tracking-widest uppercase text-primary hover:underline'>
              Register Now
            </Link>
          </p>
        </div>

        <div className='mt-20'>
          <Link
            to='/'
            className='text-xs font-bold tracking-widest uppercase transition-opacity opacity-20 hover:opacity-100'>
            Back to Home
          </Link>
        </div>
      </div>
    </main>
  );
}
