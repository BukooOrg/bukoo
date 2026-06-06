import { Loader2, Eye, EyeOff, Lock, AlertCircle, ShieldAlert } from 'lucide-react';
import React, { useState } from 'react';
import { toast } from 'sonner';

import { PasswordStrengthMeter } from '@/components/auth/password-strength-meter';
import { useAuth } from '@/context/AuthContext';
import { useApiMutation } from '@/hooks/useApiMutation';
import { userApi } from '@/lib/apiClient';

export default function PasswordPage() {
  const { user } = useAuth();

  if (user && !user.havePassword) {
    return (
      <div className='text-center py-16 space-y-4'>
        <ShieldAlert className='w-12 h-12 mx-auto text-muted-foreground' />
        <h2 className='text-2xl font-serif font-black text-primary'>No Password Needed</h2>
        <p className='text-sm text-muted-foreground max-w-md mx-auto'>
          Your account uses Google or Facebook login, so there&apos;s no local password to change.
          If you lost access to your social account, contact support.
        </p>
      </div>
    );
  }

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');

  const {
    mutate: changePassword,
    loading,
    error: mutationError,
  } = useApiMutation((variables) => userApi.changePassword(variables), {
    onSuccess: () => {
      toast.success('Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setError('');
    },
    onError: (err) => {
      const msg =
        err?.response?.data?.error?.message || err?.message || 'Failed to change password';
      console.error('Password change error:', err);
      setError(msg);
    },
  });

  const validatePassword = (pwd) => {
    if (pwd.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(pwd)) return 'Must contain an uppercase letter';
    if (!/[a-z]/.test(pwd)) return 'Must contain a lowercase letter';
    if (!/[0-9]/.test(pwd)) return 'Must contain a number';
    if (!/[^A-Za-z0-9]/.test(pwd)) return 'Must contain a special character';
    return '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!currentPassword) {
      setError('Current password is required');
      return;
    }

    const pwdError = validatePassword(newPassword);
    if (pwdError) {
      setError(pwdError);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    changePassword({
      changePasswordRequest: {
        currentPassword,
        newPassword,
      },
    });
  };

  const pwdError = validatePassword(newPassword);

  return (
    <div className='space-y-8'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Change Password
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>Update your account password</p>
      </div>

      <div className='max-w-lg mx-auto'>
        <form onSubmit={handleSubmit} className='space-y-5'>
          {/* Current Password */}
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Current Password
            </label>
            <div className='relative group'>
              <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                <Lock className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
              </div>
              <input
                type={showCurrent ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder='Enter current password'
                className='w-full pl-12 pr-14 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
              />
              <button
                type='button'
                onClick={() => setShowCurrent(!showCurrent)}
                className='absolute right-4 top-1/2 -translate-y-1/2 text-primary/30 hover:text-primary transition-colors'>
                {showCurrent ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
              </button>
            </div>
          </div>

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
                type={showNew ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder='Min. 8 characters'
                className='w-full pl-12 pr-14 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
              />
              <button
                type='button'
                onClick={() => setShowNew(!showNew)}
                className='absolute right-4 top-1/2 -translate-y-1/2 text-primary/30 hover:text-primary transition-colors'>
                {showNew ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
              </button>
            </div>
            <PasswordStrengthMeter password={newPassword} />
          </div>

          {/* Confirm New Password */}
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Confirm New Password
            </label>
            <div className='relative group'>
              <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                <Lock className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
              </div>
              <input
                type={showConfirm ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder='Re-enter new password'
                className='w-full pl-12 pr-14 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
              />
              <button
                type='button'
                onClick={() => setShowConfirm(!showConfirm)}
                className='absolute right-4 top-1/2 -translate-y-1/2 text-primary/30 hover:text-primary transition-colors'>
                {showConfirm ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
              </button>
            </div>
            {confirmPassword && confirmPassword !== newPassword && (
              <p className='text-xs font-bold text-destructive pl-1'>Passwords do not match</p>
            )}
          </div>

          {/* Error Message */}
          {(error || mutationError) && (
            <div className='flex items-start gap-3 p-4 duration-300 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
              <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
              <p className='text-xs font-bold leading-relaxed text-destructive'>
                {error || mutationError?.message || 'An error occurred'}
              </p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type='submit'
            disabled={
              loading ||
              !currentPassword ||
              !newPassword ||
              !confirmPassword ||
              !!pwdError ||
              newPassword !== confirmPassword
            }
            className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
            {loading ? (
              <Loader2 className='w-5 h-5 animate-spin' />
            ) : (
              <>
                <Lock className='w-5 h-5' />
                <span>Change Password</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
