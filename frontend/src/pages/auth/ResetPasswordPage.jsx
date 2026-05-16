import { ResponseError } from '@bukoo/api-client';
import { Lock, CheckCircle, AlertCircle, Loader2, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { PasswordStrengthMeter } from '@/components/auth/password-strength-meter';
import { useApiMutation } from '@/hooks/useApiMutation';
import { authApi } from '@/lib/apiClient';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [confirmError, setConfirmError] = useState('');

  const email = searchParams.get('email') || '';
  const otp = searchParams.get('otp') || '';

  const { mutate: resetPassword, loading: isSubmitting } = useApiMutation(
    (variables) => authApi.resetPassword(variables),
    {
      onSuccess: () => {
        setSuccess(true);
        toast.success('Password reset successful!');
        setTimeout(() => navigate('/login'), 3000);
      },
      onError: (err) => {
        if (err instanceof ResponseError) {
          err.response?.json?.().then((data) => {
            setError(data?.error?.message || 'Failed to reset password');
          });
        } else {
          setError('Something went wrong. Please try again later.');
        }
      },
    }
  );

  const validatePassword = (value) => {
    if (value.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(value)) return 'Must contain an uppercase letter';
    if (!/[a-z]/.test(value)) return 'Must contain a lowercase letter';
    if (!/[0-9]/.test(value)) return 'Must contain a number';
    if (!/[^A-Za-z0-9]/.test(value)) return 'Must contain a special character';
    return '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    const pwdError = validatePassword(password);
    if (pwdError) {
      setPasswordError(pwdError);
      return;
    }

    if (password !== confirmPassword) {
      setConfirmError('Passwords do not match');
      return;
    }

    if (!email || !otp) {
      setError('Invalid reset link. Please request a new one.');
      return;
    }

    setPasswordError('');
    setConfirmError('');
    resetPassword({ resetPasswordRequest: { email, otp, newPassword: password } });
  };

  const handlePasswordChange = (e) => {
    const value = e.target.value;
    setPassword(value);
    setPasswordError(validatePassword(value));
    if (confirmPassword && value !== confirmPassword) {
      setConfirmError('Passwords do not match');
    } else {
      setConfirmError('');
    }
  };

  const handleConfirmChange = (e) => {
    const value = e.target.value;
    setConfirmPassword(value);
    if (value !== password) {
      setConfirmError('Passwords do not match');
    } else {
      setConfirmError('');
    }
  };

  if (success) {
    return (
      <main className='relative min-h-screen overflow-hidden font-sans bg-background pt-28'>
        <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
        <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

        <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
          <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
            <div className='flex justify-center mb-6'>
              <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
                <CheckCircle className='w-7 h-7 text-green-600' />
              </div>
            </div>

            <div className='mb-10 text-center'>
              <h1 className='mb-3 font-serif text-5xl font-black tracking-tighter text-primary'>
                Password Reset!
              </h1>
              <p className='text-sm italic font-bold text-primary/40'>
                Your password has been reset successfully
              </p>
            </div>

            <div className='space-y-6'>
              <div className='p-4 border bg-green-50 border-green-200 rounded-2xl'>
                <p className='text-sm font-bold text-green-800 text-center'>
                  You can now login with your new password.
                </p>
              </div>
              <Link
                to='/login'
                className='block w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all text-center'>
                Go to Login
              </Link>
            </div>

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

  return (
    <main className='relative min-h-screen overflow-hidden font-sans bg-background pt-28'>
      <div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
      <div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />

      <div className='relative min-h-[90vh] flex flex-col items-center justify-center p-6 bg-transparent z-10'>
        <div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12 rounded-[40px] border border-white/40 shadow-2xl transition-all animate-in fade-in zoom-in duration-700'>
          <div className='flex justify-center mb-6'>
            <div className='flex items-center justify-center rounded-full w-14 h-14 bg-primary/5'>
              <Lock className='w-7 h-7 text-primary' />
            </div>
          </div>

          <div className='mb-10 text-center'>
            <h1 className='mb-3 font-serif text-5xl font-black tracking-tighter text-primary'>
              Reset Password
            </h1>
            <p className='text-sm italic font-bold text-primary/40'>
              Create a new strong password for your account
            </p>
          </div>

          <form onSubmit={handleSubmit} className='space-y-5'>
            {/* New Password */}
            <div className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                New Password
              </label>
              <div className='relative group'>
                <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                  <Lock className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={handlePasswordChange}
                  required
                  placeholder='Enter new password'
                  className='w-full pl-12 pr-12 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
                />
                <button
                  type='button'
                  onClick={() => setShowPassword(!showPassword)}
                  className='absolute inset-y-0 right-0 pr-4 flex items-center text-primary/40 hover:text-primary transition-colors'>
                  {showPassword ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
                </button>
              </div>
              <PasswordStrengthMeter password={password} />
              {passwordError && (
                <p className='text-xs font-bold text-destructive pl-1'>{passwordError}</p>
              )}
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
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={handleConfirmChange}
                  required
                  placeholder='Re-enter new password'
                  className='w-full pl-12 pr-12 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
                />
                <button
                  type='button'
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className='absolute inset-y-0 right-0 pr-4 flex items-center text-primary/40 hover:text-primary transition-colors'>
                  {showConfirmPassword ? (
                    <EyeOff className='w-5 h-5' />
                  ) : (
                    <Eye className='w-5 h-5' />
                  )}
                </button>
              </div>
              {confirmError && (
                <p className='text-xs font-bold text-destructive pl-1'>{confirmError}</p>
              )}
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
              disabled={
                !password || !confirmPassword || passwordError || confirmError || isSubmitting
              }
              className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
              {isSubmitting ? (
                <Loader2 className='w-5 h-5 animate-spin' />
              ) : (
                <>
                  <CheckCircle className='w-5 h-5' />
                  <span>Reset Password</span>
                </>
              )}
            </button>

            {/* Back to Login */}
            <div className='text-center pt-4'>
              <Link
                to='/login'
                className='text-xs font-bold text-primary/60 hover:text-primary hover:underline transition-colors'>
                Remember your password? <span className='font-black'>Login</span>
              </Link>
            </div>
          </form>

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
