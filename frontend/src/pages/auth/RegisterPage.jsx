import { ResponseError } from '@bukoo/api-client';
import { User, Lock, Mail, UserPlus, AlertCircle, Loader2 } from 'lucide-react';
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useAuth } from '@/context/AuthContext';
import { authApi } from '@/lib/apiClient';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const email = formData.get('email');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirm_password');
    const fullName = formData.get('full_name');
    const dateOfBirth = formData.get('date_of_birth');

    // Client-side validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    try {
      const response = await authApi.register({
        registerCustomerRequest: {
          email,
          password,
          confirmPassword,
          fullName,
          dateOfBirth: new Date(dateOfBirth),
        },
      });

      if (login) {
        login(response.data);
      }

      toast.success('Registration successful! Please check your email to verify your account.');
      navigate('/verify-email', { state: { email } });
    } catch (err) {
      console.error(err);
      if (err instanceof ResponseError) {
        const errorData = await err.response?.json?.();
        setError(errorData?.error?.message || 'Registration failed');
      } else {
        setError('Something went wrong. Please try again later.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className='min-h-screen bg-background relative overflow-hidden font-sans pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          <div className='text-center mb-10'>
            <div className='flex justify-center mb-6'>
              <div className='w-14 h-14 bg-primary/5 rounded-full flex items-center justify-center'>
                <UserPlus className='w-7 h-7 text-primary' />
              </div>
            </div>
            <h1 className='text-5xl font-serif font-black mb-3 text-primary tracking-tighter'>
              Join Bukoo
            </h1>
            <p className='text-primary/40 font-bold italic text-sm'>
              Start your reading journey today
            </p>
          </div>

          <form onSubmit={handleSubmit} className='space-y-5'>
            {/* Full Name */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Full Name
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <User className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                </div>
                <input
                  type='text'
                  name='full_name'
                  required
                  placeholder='Enter your name'
                  className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
                />
              </div>
            </div>

            {/* Email */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Email Address
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <Mail className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                </div>
                <input
                  type='email'
                  name='email'
                  required
                  placeholder='Enter your email'
                  className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
                />
              </div>
            </div>

            {/* Date of Birth */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Date of Birth
              </label>
              <div className='relative group'>
                <input
                  type='date'
                  name='date_of_birth'
                  required
                  className='w-full px-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
                />
              </div>
            </div>

            {/* Password */}
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
                  minLength={8}
                  placeholder='Min. 8 characters'
                  className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                Confirm Password
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <Lock className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                </div>
                <input
                  type='password'
                  name='confirm_password'
                  required
                  minLength={8}
                  placeholder='Re-enter password'
                  className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
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
              disabled={isLoading}
              className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
              {isLoading ? (
                <Loader2 className='w-5 h-5 animate-spin' />
              ) : (
                <>
                  <UserPlus className='w-5 h-5' />
                  <span>Create Account</span>
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className='mt-10 text-xs font-bold text-center text-primary/40'>
            Already have an account?{' '}
            <Link
              to='/login'
              className='ml-1 font-black tracking-widest uppercase text-primary hover:underline'>
              Login
            </Link>
          </p>
        </div>

        {/* Back to Home */}
        <div className='mt-20 text-center'>
          <Link
            to='/'
            className='text-xs font-bold tracking-widest uppercase transition-opacity opacity-20 hover:opacity-100 inline-flex items-center gap-2'>
            <span>Back to Home</span>
          </Link>
        </div>
      </div>
    </main>
  );
}
