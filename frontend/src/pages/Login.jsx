import { User, Lock, LogIn, AlertCircle, Loader2 } from 'lucide-react';
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { loginAction } from '@/actions/auth';
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

    const result = await loginAction(email, password);

    if (result.success) {
      if (login) login(result.user);
      navigate('/');
    } else {
      setError(result.error);
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
    <main className='min-h-screen bg-background relative overflow-hidden font-sans pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          <div className='text-center mb-10'>
            <div className='flex justify-center mb-6'>
              <div className='w-14 h-14 bg-primary/5 rounded-full flex items-center justify-center'>
                <LogIn className='w-7 h-7 text-primary' />
              </div>
            </div>
            <h1 className='text-5xl font-serif font-black mb-3 text-primary tracking-tighter'>
              Welcome
            </h1>
            <p className='text-primary/40 font-bold italic text-sm'>Access your Bukoo account</p>
          </div>

          <form onSubmit={handleSubmit} className='space-y-6'>
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Email Address
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <User className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                </div>
                <input
                  type='email'
                  name='email'
                  required
                  placeholder='Enter your email'
                  className='w-full pl-12 pr-4 py-4 md:py-5 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
                />
              </div>
            </div>

            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Password
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <Lock className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                </div>
                <input
                  type='password'
                  name='password'
                  required
                  placeholder='Enter your password'
                  className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-medium'
                />
              </div>
            </div>

            <div className='flex items-center justify-between px-1'>
              <label className='flex items-center gap-3 cursor-pointer group'>
                <input
                  type='checkbox'
                  className='w-5 h-5 rounded-lg border-primary/10 text-primary focus:ring-primary/20'
                />
                <span className='text-xs font-bold text-primary/40 group-hover:text-primary transition-colors'>
                  Remember me
                </span>
              </label>
              <Link to='#' className='text-xs font-black text-primary hover:underline'>
                Forgot Password?
              </Link>
            </div>

            {error && (
              <div className='bg-destructive/5 border border-destructive/10 rounded-2xl p-4 flex items-start gap-3 animate-in slide-in-from-top-2 duration-300'>
                <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
                <p className='text-xs font-bold text-destructive leading-relaxed'>{error}</p>
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

          {/* Divider */}
          <div className='flex items-center gap-4 my-6'>
            <div className='flex-1 h-px bg-primary/10' />
            <span className='text-[11px] font-black uppercase tracking-[0.2em] text-primary/30'>
              or
            </span>
            <div className='flex-1 h-px bg-primary/10' />
          </div>

          {/* OAuth buttons */}
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

          <p className='text-center text-xs text-primary/40 font-bold mt-10'>
            Don't have an account?{' '}
            <Link
              to='/register'
              className='text-primary font-black hover:underline uppercase tracking-widest ml-1'>
              Register Now
            </Link>
          </p>
        </div>

        <div className='mt-20'>
          <Link
            to='/'
            className='text-xs font-bold uppercase tracking-widest opacity-20 hover:opacity-100 transition-opacity'>
            Back to Home
          </Link>
        </div>
      </div>
    </main>
  );
}
